import json
import uuid
from datetime import datetime

import requests

from libraries.common import log_message
from libraries.utils import (BadRequestException,
                            ScheduledMaintenanceException,
                             retry_if_bad_request)


class CentralReachRequests:

    def __init__(self, credentials: dict):
        """ Create session and login to "Central Reach" site
        :param credentials: dict with keys "login" and "password"
        """
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.session = requests.session()
        self.login_by_request()

    @staticmethod
    def __get_guid() -> str:
        return str(uuid.uuid4())

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
            self.__login_to_central_reach()
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
    def __login_to_central_reach(self) -> None:
        log_url = 'https://members.centralreach.com/api/?framework.login'
        payload = {
            "username": self.login,
            "password": self.password,
            "subdomain": "members",
        }
        response = self.session.post(log_url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with registration on the 'Central Reach' site"
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)

        if response.json().get('success', False) is not True:
            raise BadRequestException(exception_message)

    @retry_if_bad_request
    def logout_from_central_reach(self) -> None:
        log_url = 'https://members.centralreach.com/api/?framework.logout'
        response = self.session.post(log_url,  headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with logout from the 'Central Reach' site"

        if response.status_code != 200:
            raise BadRequestException(exception_message)


    def __insurance_eligibility_status(self) -> None:
        header = {'referer': 'https://members.centralreach.com/'}
        url = 'https://members.centralreach.com/crxapi/system/dictionary/InsuranceEligibilityStatus'
        response = self.session.get(url, headers=self.__get_headers(is_json=True, add_headers=header))

        exception_message = f"Problems with insurance eligibility request."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)

    def get_filters(self):
        payload = {
            "applicationSection": "billingmanager.billing",
        }
        url = 'https://members.centralreach.com/api/?shared.loadFilters'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with getting filters."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()['filters']

    def get_filter_by_name(self, filter_name):
        filters = self.get_filters()
        for filter_data in filters:
            if str(filter_data['Name']).strip() == filter_name:
                return json.loads(filter_data['filters'])
        else:
            raise Exception(f"Filter {filter_name} doesn't exist")

    def get_payors_of_billing_page(self, start_date: datetime, end_date: datetime, page_filter: dict = None):
        if page_filter is not None:
            payload = page_filter
        else:
            payload = {}

        payload.update({
            "dateRange": f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}",
            "startDate": start_date.strftime('%Y-%m-%d'),
            "endDate": end_date.strftime('%Y-%m-%d'),
            'type': "insurances",
            "page": '1',
            "pageSize": '30000'
        })

        url = 'https://members.centralreach.com/api/?billingmanager.loadBillingListDistincts'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with getting payors of billing page."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()['insurances']

    def get_billings(self, start_date: datetime, end_date: datetime, page_filter: dict = None):
        if page_filter is not None:
            payload = page_filter
        else:
            payload = {}
        payload.update({
            "dateRange": f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}",
            "startDate": start_date.strftime('%Y-%m-%d'),
            "endDate": end_date.strftime('%Y-%m-%d'),
            "page": '1',
            "pageSize": '30000'
        })
        url = 'https://members.centralreach.com/crxapi/internal/billing/query'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with getting billings."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()['items']

    def get_labels(self):
        url = 'https://members.centralreach.com/api/?billingmanager.timesheetloadlabels'
        response = self.session.post(url, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with getting labels."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()['labels']

    def get_providers(self, start_date: datetime, end_date: datetime, page_filter: dict = None):
        if page_filter is not None:
            payload = page_filter
        else:
            payload = {}

        payload.update({
            "dateRange": f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}",
            "startDate": start_date.strftime('%Y-%m-%d'),
            "endDate": end_date.strftime('%Y-%m-%d'),
            'type': "providers",
            "page": '1',
            "pageSize": '30000'
        })

        url = 'https://members.centralreach.com/api/?billingmanager.loadBillingListDistincts'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with getting providers."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()['providers']


    def get_payor_bulk_claims(self, start_date: datetime, end_date: datetime, page_filter: dict = None):
        if page_filter is not None:
            payload = page_filter
        else:
            payload = {}
        payload.update({
            "dateRange": f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}",
            "startDate": start_date.strftime('%Y-%m-%d'),
            "endDate": end_date.strftime('%Y-%m-%d'),
            "page": '1',
            "pageSize": '30000'
        })
        url = 'https://members.centralreach.com/api/?claims.loadbulkgenerateclaims'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with getting payor bulk claims."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()['list']


    def get_claims_inbox(self,start_date: datetime, end_date: datetime, page_filter: dict = None):
        if page_filter is not None:
            payload = page_filter
        else:
            payload = {}
        payload.update({
            "dateRange": f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}",
            "startDate": start_date.strftime('%Y-%m-%d'),
            "endDate": end_date.strftime('%Y-%m-%d'),
            "page": '1',
            "pageSize": '30000'
        })
        url = 'https://members.centralreach.com/crxapi/claims/loadlist'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with getting claims inbox."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()['items']

    def login_by_request(self):
        self.__login_to_central_reach()
        self.__insurance_eligibility_status()

