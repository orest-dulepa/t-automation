import json
import time
from datetime import datetime, timedelta

import requests

from libraries.common import log_message
from libraries.utils import (BadRequestException,
                             ScheduledMaintenanceException,
                             retry_if_bad_request)


class CentralReachRequests:

    def __init__(self):
        """ Create session and login to "Central Reach" site
        :param credentials: dict with keys "login" and "password"
        """
        self.start_date: datetime = datetime.now() - timedelta(days=7)
        self.end_date: datetime = datetime.now()
        self.default_filter_name = ''
        self.__common_search_filter: dict = None
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

    @classmethod
    def __check_response(cls, response, mandatory_json=False, exc_message='') -> None:
        if cls.__is_scheduled_maintenance(response):
            log_message(exc_message, 'Error')
            log_message("'Central Reach' site is currently unavailable due to scheduled maintenance", 'Error')
            raise ScheduledMaintenanceException

        elif response.status_code == 401:
            cls._login_to_central_reach()
            raise BadRequestException(f"{exc_message}Status Code: {response.status_code} (Unauthorized request), "
                                      f"Json content: {response.json()}, Headers: {response.headers}")

        if response.status_code != 200 or (mandatory_json and not cls.__is_json_response(response)):
            exc_message = exc_message + '\n' if exc_message else ''
            if cls.__is_json_response(response):
                raise BadRequestException(f"{exc_message}Status Code: {response.status_code}, "
                                          f"Json content: {response.json()}, Headers: {response.headers}")
            else:
                raise BadRequestException(f"{exc_message}Status Code: {response.status_code}, "
                                          f"Headers: {response.headers}")

    @retry_if_bad_request
    def _login_to_central_reach(self, login, password) -> None:
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

    @retry_if_bad_request
    def _insurance_eligibility_status(self) -> None:
        header = {'referer': 'https://members.centralreach.com/'}
        url = 'https://members.centralreach.com/crxapi/system/dictionary/InsuranceEligibilityStatus'
        response = self.session.get(url, headers=self.__get_headers(is_json=True, add_headers=header))

        exception_message = f"Problems with insurance eligibility request."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)

    @retry_if_bad_request
    def __get_filters(self):
        payload = {
            "applicationSection": "billingmanager.billing",
        }
        url = 'https://members.centralreach.com/api/?shared.loadFilters'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with getting billings."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()['filters']

    def _default_search_filter(self):
        if not self.default_filter_name:
            return {}
        if self.__common_search_filter is None:
            log_message(f"Apply filter '{self.default_filter_name}'")
            self.__common_search_filter: dict = self._get_filter_by_name(self.default_filter_name)
            del self.__common_search_filter['dateRange']
        search_filter = self.__common_search_filter.copy()
        return search_filter

    def _get_filter_by_name(self, filter_name):
        filters = self.__get_filters()
        for filter_data in filters:
            if str(filter_data['Name']).strip() == filter_name:
                return json.loads(filter_data['filters'])
        else:
            raise Exception(f"Filter '{filter_name}' doesn't exist")

    @retry_if_bad_request
    def _load_billing_list_distincts(self):
        payload = self._default_search_filter()
        payload.update({
            "startDate": self.start_date.strftime('%Y-%m-%d'),
            "endDate": self.end_date.strftime('%Y-%m-%d'),
            "page": '1',
            "pageSize": '5000',
            "type": "clients"
        })
        url = 'https://members.centralreach.com/api/?billingmanager.loadBillingListDistincts'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with getting clients list."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()['clients']

    @retry_if_bad_request
    def _load_bulk_invoice(self, client_id):
        payload = self._default_search_filter()
        payload.update({
            "startDate": self.start_date.strftime('%Y-%m-%d'),
            "endDate": self.end_date.strftime('%Y-%m-%d'),
            "clientId": client_id,
            "sort": "date",
            "type": "clients",
            "typeId": "clientId",
            "loadAll": True,
            "ignore": ["data", "items"],
            "_track": {'action': "billing/invoices", 'channel': "billingmanager"}
        })
        url = 'https://members.centralreach.com/api/?billingmanager.loadbulkinvoice'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with loading balk invoice count."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()

    @retry_if_bad_request
    def _set_bulk_invoice(self, bill_from_id, bill_to_id, client_id, due_date: datetime):
        # Button "Bulk-generate Patient Responsibility Invoices"
        search_filter = self._default_search_filter()
        search_filter.update({
            "startDate": self.start_date.strftime('%Y-%m-%dT%H:%M:%S.%f'),
            "endDate": self.end_date.strftime('%Y-%m-%dT%H:%M:%S.%f'),
            "clientId": client_id,
        })

        payload = {
            "groups": [{
                "billFromId": bill_from_id,
                "billToId": bill_to_id,
                "dueDate": due_date.strftime('%m/%d/%Y'),
                "keyId": client_id,
                "type": "copay",
                "entryIds": "-1"
            }],
            "search": [search_filter],
            "_track": {
                'action': "billing/invoices/generate",
                'channel': "billingmanager"
            }
        }
        url = 'https://members.centralreach.com/api/?billingmanager.setbulkinvoice'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with loading balk invoice count."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()['invoiceIds'][0]

    @retry_if_bad_request
    def _load_invoice(self, invoice_id):
        payload = {"invoiceId": invoice_id}

        url = 'https://members.centralreach.com/api/?billingmanager.loadinvoice'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with load invoice"
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()

    @retry_if_bad_request
    def _set_invoice_notes(self, invoice_id: int, notes: str):
        payload = {
            "invoiceId": invoice_id,
            "notes": notes
        }
        url = 'https://members.centralreach.com/api/?billingmanager.setinvoicenotes'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with setting invoice notes"
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)

    @retry_if_bad_request
    def _export_invoice(self, invoice_id):
        with open(r'libraries/print_invoice_settings.json') as json_file:
            invoice_settings = json.load(json_file)
        invoice_settings.update({
            'invoiceId': invoice_id,
            'selectedColumns': ["date", "provider", "service", "location", "units", "copay"],
            'globalNotes': "<p>If you have any questions or would like to make a payment, reach out to our accounting "
                           "office at 800-249-1255 or email us at accounting@behavioralhealthworks.com</p>"
        })
        payload = [invoice_settings]

        url = 'https://members.centralreach.com/api/?billingmanager.exportInvoice'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with generation invoice"
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)

    @retry_if_bad_request
    def _wait_for_invoice_is_ready(self, invoice_id: int):
        url = f'https://members.centralreach.com/crxapi/invoice/status/{invoice_id}'
        finish_wait_time = datetime.now() + timedelta(seconds=30)
        while True:
            response = self.session.get(url, headers=self.__get_headers(is_json=True))
            self.__check_response(response, mandatory_json=True)
            if response.json()['resourceId']:
                return response.json()['resourceId']
            elif response.json()['failed'] is True:
                raise Exception(f"Preparing invoice is failed, status: {response.json()['status']}")
            elif datetime.now() > finish_wait_time:
                raise Exception(f"Generation invoice {invoice_id} is timeout, status: {response.json()['status']}")
            time.sleep(1)

    def _load_contact_details(self, contact_id: int):
        payload = {'id': contact_id}
        url = 'https://members.centralreach.com/api/?contacts.loadcontactdetails'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exc_message = 'Problems with loading contact details'
        self.__check_response(response, mandatory_json=True, exc_message=exc_message)
        return response.json()['contact']

    def __get_download_link(self, resource_id):
        payload = {'resourceIds': [resource_id]}
        url = 'https://members.centralreach.com/crxapi/invoice/combinepdfs'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exc_message = 'Problems with getting url for download invoice'
        self.__check_response(response, mandatory_json=True, exc_message=exc_message)
        return response.json()['downloadUrl']

    @retry_if_bad_request
    def _download_invoice(self, resource_id, path_to_file):
        url = self.__get_download_link(resource_id)
        response = self.session.get(url)
        exc_message = 'Problems with invoice downloading'
        self.__check_response(response, exc_message=exc_message)

        with open(path_to_file, 'wb') as f:
            f.write(response.content)

    @retry_if_bad_request
    def _get_billings(self, client_id: int = 0):
        payload = self._default_search_filter()
        payload.update({
            "dateRange": f"{self.start_date.strftime('%b %d')} - {self.end_date.strftime('%b %d')}",
            "startDate": self.start_date.strftime('%Y-%m-%d'),
            "endDate": self.end_date.strftime('%Y-%m-%d'),
            "ClientId": client_id,
            "page": '1',
            "pageSize": '1',
        })
        url = 'https://members.centralreach.com/crxapi/internal/billing/query'
        response = self.session.post(url, json=payload, headers=self.__get_headers(is_json=True))

        exception_message = f"Problems with getting billings."
        self.__check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()['items']
