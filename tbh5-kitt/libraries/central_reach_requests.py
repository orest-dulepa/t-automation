import datetime
import json
import uuid
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
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.session = requests.session()
        self.__login_to_central_reach()

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
    def get_era_list(self, start_date: datetime = None, end_date: datetime = None):
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
        if response.status_code != 200:
            response = self.session.get(load_era_list_url, json=data)

        if 'application/json' in response.headers.get('content-type'):
            if response.status_code == 200 and response.json().get('success', False) is True:
                return response.json()
            elif 'message' in response.json():
                raise Exception(
                    f"Problems with getting 'Era List' from 'Central Reach' site. {response.json()['message']}")
        raise Exception(f"Problems with getting 'Era List' from 'Central Reach' site.")

    def get_zero_pay_filter(self, start_date: datetime = None, end_date: datetime = None) -> dict:
        response = self.get_era_list(start_date, end_date)
        era_list_data = response['items']

        # Zero Pay filter
        zero_pay_data: dict = {}
        for item in era_list_data:
            if item['PaymentAmount'] == .0:
                zero_pay_data[str(item['Id'])] = item
        return zero_pay_data

    def get_pr_filter(self, start_date: datetime = None, end_date: datetime = None) -> dict:
        response = self.get_era_list(start_date, end_date)
        era_list_data = response['items']

        # PR filter
        pr_data: dict = {}
        for item in era_list_data:
            if item['PaymentAmount'] == .0 and item['PrAdjustmentTotal'] > 0 and item['PiAdjustmentTotal'] == .0 and \
                    item['Reconciled'] == 'None':
                pr_data[str(item['Id'])] = item
        return pr_data

    def get_denial_filter(self, start_date: datetime = None, end_date: datetime = None) -> dict:
        response = self.get_era_list(start_date, end_date)
        era_list_data = response['items']

        # Denial filter
        denial_data: dict = {}
        for item in era_list_data:
            if item['PaymentAmount'] == .0 and item['Reconciled'] == 'None':
                denial_data[str(item['Id'])] = item
        return denial_data
