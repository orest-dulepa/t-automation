import datetime
import re


class Timesheet:

    def __init__(self, timesheet_id: str):
        self.timesheet_id: str = timesheet_id
        self.client_id: str = ''
        self.client_name: str = ''
        self.date: str = ''
        self.date_of_service: datetime = None

        self.current_payor: str = ''
        self.service_code: str = ''
        self.service_dscrpt: str = ''

        self.owed: float = .0
        self.pr_amount: float = .0
        self.agreed: float = .0
        self.billed: float = .0
        self.paid: float = .0

        self.eob: dict = {}

        self.processed: bool = False

    def set_date_and_time(self, date: str):
        self.date: str = date
        self.date_of_service: datetime = datetime.datetime.strptime(date, '%m/%d/%y')

    def set_service(self, service: str):
        self.service_code: str = service.split(':')[0].strip().upper()
        self.service_dscrpt: str = service[service.index(':') + 1:].strip()

        self.service_dscrpt = self.service_dscrpt.split('-')[0].replace('(EVV)', '').strip()

    def __str__(self):
        return self.timesheet_id
