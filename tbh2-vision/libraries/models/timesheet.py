import datetime
import re
from libraries.models.insurance import Insurance
from libraries.models.client import Client
from libraries.models.provider import Provider


class Timesheet:

    def __init__(self, timesheet_id: str):
        self.timesheet_id: str = timesheet_id
        self.client: Client = None
        self.provider: Provider = None
        self.date: str = ''
        self.date_of_service: datetime = None
        self.start_time: datetime = None
        self.end_time: datetime = None
        self.time: str = ''
        self.current_payor: str = ''
        self.primary_payor: Insurance = None
        self.secondary_payor: Insurance = None
        # Position of the secondary payor if same name exist
        self.position_of_secondary_payor = 0
        self.service_code: str = ''
        self.service_dscrpt: str = ''
        self.owed: float = .0
        self.payment_count: int = 0
        self.secondary_claim: bool = False
        self.billed: float = .0
        self.location: str = ''
        self.amount_paid: float = 0.0

        self.modifiers: str = ''
        self.claim_id: str = ''
        self.is_valid: bool = True

    def set_date_and_time(self, date: str, time: str):
        self.date: str = date
        self.time: str = time
        self.date_of_service: datetime = datetime.datetime.strptime(date, '%m/%d/%y')
        self.convert_time()

    def set_service(self, service: str):
        try:
            self.service_code: str = service.split(':')[0].strip().upper()
            self.service_dscrpt: str = service[service.index(':') + 1:].strip()
            self.service_dscrpt = self.service_dscrpt.split('-')[0].replace('(EVV)', '').strip()
        except:
            pass

    def __str__(self):
        return self.timesheet_id

    def convert_time(self):
        match_time = re.search(r'(?i)(\d+:\d{2}|\d+)(a|p|)-(\d+:\d{2}|\d+)(a|p|)( (\w{3})|)', self.time)
        start_hours = match_time[1] if ':' in match_time[1] else match_time[1] + ':00'
        start_am_pm = match_time[2] if len(match_time[2]) > 0 else match_time[4]
        start_am_pm = 'AM' if start_am_pm == 'a' else 'PM'
        end_hours = match_time[3] if ':' in match_time[3] else match_time[3] + ':00'
        end_am_pm = 'AM' if match_time[4] == 'a' else 'PM'

        self.start_time = datetime.datetime.strptime('{} {} {}'.format(
            self.date, start_hours, start_am_pm), '%m/%d/%y %I:%M %p'
        )
        self.end_time = datetime.datetime.strptime('{} {} {}'.format(
            self.date, end_hours, end_am_pm), '%m/%d/%y %I:%M %p'
        )

    def check_overlap(self, timesheet) -> bool:
        if self.current_payor.lower() != timesheet.current_payor.lower():
            return False
        if self.start_time <= timesheet.start_time < self.end_time \
                or self.start_time < timesheet.end_time <= self.end_time:
            return True
        return False

    def set_insurances(self):
        for insurance in self.client.insurances:
            if insurance.valid_from <= self.date_of_service <= insurance.valid_to:
                if insurance.is_primary and not self.primary_payor:
                    self.primary_payor = insurance
                if not insurance.is_primary and not self.secondary_payor:
                    self.secondary_payor = insurance

    def set_position_of_secondary_insurance(self, valid_insurance: Insurance):
        for insurance in self.client.insurances:
            if insurance.payer_name == valid_insurance.payer_name and not insurance.is_primary:
                self.position_of_secondary_payor += 1
            if insurance == valid_insurance:
                break
        if self.position_of_secondary_payor == 0:
            self.position_of_secondary_payor = 1

    def set_rate(self, rate: float) -> None:
        if self.current_payor not in self.provider.rates:
            self.provider.rates[self.current_payor] = {}
        if self.service_code not in self.provider.rates[self.current_payor]:
            self.provider.rates[self.current_payor][self.service_code] = rate

    def get_rate(self) -> float or None:
        if self.current_payor in self.provider.rates and self.service_code in self.provider.rates[self.current_payor]:
            return self.provider.rates[self.current_payor][self.service_code]
        return None
