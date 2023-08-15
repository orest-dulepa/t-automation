import json
from datetime import datetime

import requests

from libraries.common import log_message
from libraries.utils import retry_if_bad_request, BadRequestException, ScheduledMaintenanceException


class CentralReachRequests:
    def __init__(self):
        self.session = requests.session()

    @staticmethod
    def __get_headers(is_json=True, add_headers: dict = None) -> dict:
        headers = {}
        if is_json:
            headers['content-type'] = 'application/json; charset=UTF-8'
        if add_headers:
            for key, value in add_headers.items():
                headers[key] = value
        return headers

    @staticmethod
    def __is_scheduled_maintenance(response) -> bool:
        if response.status_code == 200 and 'Scheduled Maintenance' in response.text:
            return True
        return False

    @staticmethod
    def __is_json_response(response) -> bool:
        try:
            response.json()
            return True
        except json.decoder.JSONDecodeError:
            return False

    def __check_response(self, response, mandatory_json=False, exc_message='') -> None:
        if self.__is_scheduled_maintenance(response):
            log_message(exc_message, 'Error')
            log_message("'Central Reach' site is currently unavailable due to scheduled maintenance", 'Error')
            raise ScheduledMaintenanceException

        elif response.status_code == 401:
            self._login_to_central_reach()
            raise BadRequestException(f"{exc_message}Status Code: {response.status_code} (Unauthorized request), "
                                      f"Json content: {response.json()}, Headers: {response.headers}")

        if response.status_code != 200 or (mandatory_json and not self.__is_json_response(response)):
            exc_message = exc_message + '\n' if exc_message else ''
            if self.__is_json_response(response):
                raise BadRequestException(f"{exc_message}Status Code: {response.status_code}, "
                                          f"Json content: {response.json()}, Headers: {response.headers}")
            else:
                raise BadRequestException(f"{exc_message}Status Code: {response.status_code}, "
                                          f"Headers: {response.headers}")

    @retry_if_bad_request
    def _login_to_central_reach(self, login: str, password: str) -> None:
        log_url = 'https://members.centralreach.com/api/?framework.login'
        payload = {
            "username": login,
            "password": password,
            "subdomain": "members",
        }
        response = self.session.post(log_url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with registration on the 'Central Reach' site"
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)

        if response.json().get('success', False) is not True:
            raise BadRequestException(exception_message)

    def __insurance_eligibility_status(self) -> None:
        header = {'referer': 'https://members.centralreach.com/'}
        url = 'https://members.centralreach.com/crxapi/system/dictionary/InsuranceEligibilityStatus'
        response = self.session.get(url, headers=self.__get_headers(is_json=True, add_headers=header))

        exception_message = f"Problems with insurance eligibility request."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)

    @retry_if_bad_request
    def _get_payments(self, payment_id: int, page: int) -> dict:
        self.__insurance_eligibility_status()
        params = {
            'page': page,
            'pageSize': 10,
        }
        payments_url = f'https://members.centralreach.com/crxapi/claims/era/recon/{payment_id}'
        response = self.session.get(payments_url, headers=self.__get_headers(is_json=True), params=params)

        exception_message = f"Problems with getting payments on the 'Central Reach' site for payment id {payment_id}"
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)

        return response.json()

    @retry_if_bad_request
    def _get_era_list(self, start_date: datetime = None, end_date: datetime = None) -> dict:
        _start_date = start_date.strftime('%Y-%m-%d') if start_date else ''
        _end_date = end_date.strftime('%Y-%m-%d') if start_date else ''

        load_era_list_url = 'https://members.centralreach.com/api/?claims.loadERAList'
        data = {
            "startDate": _start_date,
            "endDate": _end_date,
            "page": '1',
            "claimLabelId": '',
            "pageSize": '2000',
        }
        response = self.session.get(load_era_list_url, json=data)

        exception_message = "Problems with getting 'Era List' from 'Central Reach' site."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)

        return response.json()

    @retry_if_bad_request
    def _apply_billing_entries_changes(self, claim_line_id: str, billing_entry_ids: list) -> None:
        params = {
            'claimLineIds': [claim_line_id],
            'billingEntryIds': ','.join(map(str, billing_entry_ids)),
        }
        url = 'https://members.centralreach.com/crxapi/claims/era/recon/orphanedBillingEntries/'
        response = self.session.post(url, params=params, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with applying billing entries for claim line - {claim_line_id}"
        self.__check_response(response, exc_message=exception_message)

    @retry_if_bad_request
    def _reconcile_all_post(self, payments: list, payment_id: int) -> None:
        payload = {
            "id": payment_id,
            "payments": payments,
        }
        reconcile_url = 'https://members.centralreach.com/api/?claims.reconcilepayment'
        response = self.session.post(reconcile_url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with reconcile {len(payments)} claim lines " \
                            f"(include service line adjustment) for payment with ID - '{payment_id}'"
        self.__check_response(response, exc_message=exception_message)

    @retry_if_bad_request
    def _get_billing_entries(self, client_id: int, service_date: datetime) -> dict:
        params = {
            'clientId': client_id,
            'serviceDateStart': service_date.strftime('%Y-%m-%d'),
            'serviceDateEnd': service_date.strftime('%Y-%m-%d'),
        }
        billing_entries_url = 'https://members.centralreach.com/crxapi/claims/era/recon/billingEntries/'
        response = self.session.get(billing_entries_url, params=params, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with getting billing entries for client_id - {client_id}, " \
                            f"service date - {service_date.strftime('%Y-%m-%d')}"
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)

        return response.json()['billingEntriesResult']['billingEntries']

    @retry_if_bad_request
    def _remove_billing_entry_link(self, claim_line_id: int):
        self.__insurance_eligibility_status()
        payload = {
            'claimLineId': claim_line_id,
        }
        payments_url = f'https://members.centralreach.com/crxapi/claims/era/recon/orphanedBillingEntries/'
        response = self.session.delete(payments_url, headers=self.__get_headers(is_json=True), json=payload)

        exception_message = f"Problems with removing billing entry of claim line '{claim_line_id}'"
        self.__check_response(response, exc_message=exception_message)
