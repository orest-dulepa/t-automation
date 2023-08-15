import re
from datetime import datetime


class BillingEntry:
    def __init__(self, billing_entry_json_data):
        self.__json_data = billing_entry_json_data
        self.code = self.__json_data['code']
        self.id = self.__json_data['billingEntryId']

        self.date_from = self.get_billing_entry_date(self.__json_data['timeWorkedFrom'])
        self.date_to = self.get_billing_entry_date(self.__json_data['timeWorkedTo'])

    @staticmethod
    def get_billing_entry_date(date_string: str) -> datetime:
        search_res = re.search(r'(\d\d?)/(\d\d?)/(\d{4})', date_string)
        if search_res is None:
            raise Exception("Wrong format", search_res, date_string)

        month, day, year = search_res.groups()
        return datetime(int(year), int(month), int(day))
