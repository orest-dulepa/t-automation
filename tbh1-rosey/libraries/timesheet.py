import datetime
import re


class Timesheet:
    overlap = {}

    def __init__(self,
                 timesheet_id: str,
                 client: str,
                 date: str,
                 time: str,
                 payor: str,
                 service: str,
                 rate_agreed: str,
                 charges_agreed: str,
                 client_id: str
                 ):
        self.timesheet_id: str = timesheet_id
        self.client: str = client.strip()
        self.client_id: str = client_id
        self.date: str = date.strip()
        self.time: str = time.strip()
        self.start_time: datetime = None
        self.end_time: datetime = None
        self.payor: str = payor[3:].strip()
        self.cd_number: str = service.split(':')[0].strip()
        self.service: str = service[service.index(':') + 1:].strip()
        self.rate: float = round(float('0' + str(rate_agreed)), 2)
        self.charges: float = round(float('0' + str(charges_agreed)), 2)
        self.labels: list = []
        self.hold_whole_day: bool = False
        self.convert_time()

    def __str__(self):
        return '{} | {} | {} | {} | {} | {} | {} | {} | {} | {}'.format(
            self.client,
            self.date,
            self.time,
            self.payor,
            self.cd_number,
            self.service,
            self.rate,
            self.charges,
            self.client_id,
            str.join(', ', self.labels)
        )

    def convert_time(self):
        match_time = re.search(r'(?i)(\d+:\d{2}|\d+)(a|p|)-(\d+:\d{2}|\d+)(a|p|) (\w{3})', self.time)
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
        if self.payor.lower() != timesheet.payor.lower():
            return False
        if self.start_time <= timesheet.start_time < self.end_time \
                or self.start_time < timesheet.end_time <= self.end_time:
            return True
        return False
