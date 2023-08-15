import datetime
import re


class Timesheet:
    overlap = {}

    timezones = {
        'EDT': -4,
        'EST': -5,
        'CDT': -5,
        'CST': -6,
        'MDT': -6,
        'MST': -7,
        'PDT': -7,
        'PST': -8,
        'AKDT': -8,
        'AKST': -9,
        'HDT': -9,
        'HST': -10,
    }

    def __init__(self, client: str, date: str, time: str, payor: str, provider: str, tasks: str):
        self.client: str = client.strip()
        self.date: str = date.strip()
        self.time: str = time.strip()
        self.start_time: datetime = None
        self.end_time: datetime = None
        self.payor: str = payor[3:].strip()
        self.provider: str = provider
        self.tasks = tasks
        self.convert_time()
        self.is_need_check = False

    def __str__(self):
        return '{} | {} | {} | {} | {}'.format(self.provider, self.date, self.time, self.payor, self.is_need_check)

    def convert_time(self):
        match_time = re.search(r'(?i)(\d+:\d{2}|\d+)(a|p|)-(\d+:\d{2}|\d+)(a|p|)\s*(\w{3}|)', self.time)
        start_hours = match_time[1] if ':' in match_time[1] else match_time[1] + ':00'
        start_am_pm = match_time[2] if len(match_time[2]) > 0 else match_time[4]
        start_am_pm = 'AM' if start_am_pm == 'a' else 'PM'
        end_hours = match_time[3] if ':' in match_time[3] else match_time[3] + ':00'
        end_am_pm = 'AM' if match_time[4] == 'a' else 'PM'

        self.start_time = datetime.datetime.strptime(
            '{} {} {}'.format(self.date, start_hours, start_am_pm), '%m/%d/%y %I:%M %p'
        )
        self.end_time = datetime.datetime.strptime(
            '{} {} {}'.format(self.date, end_hours, end_am_pm), '%m/%d/%y %I:%M %p'
        )
        if match_time[5]:
            self.start_time = self.start_time + datetime.timedelta(hours=self.timezones.get(match_time[5], 0))
            self.end_time = self.end_time + datetime.timedelta(hours=self.timezones.get(match_time[5], 0))

    def check_overlap(self, timesheet) -> bool:
        if self.start_time <= timesheet.start_time < self.end_time \
                or self.start_time < timesheet.end_time <= self.end_time:
            return True
        return False
