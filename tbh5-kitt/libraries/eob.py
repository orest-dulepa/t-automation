import datetime
import re
from libraries.common import log_message


class EOB:
    def __init__(self):
        self.insurance_name: str = ''
        self.eft_number: str = ''
        # dict[reason_code] = Adjustment()
        self.adjustments: list = []
        self.date: datetime = datetime.date.today()
        self.denial: bool = False
        self.denial_code: str = ''
        self.lockbox: bool = False

    def __str__(self):
        return f'EFT: {self.eft_number} and insurance: {self.insurance_name}'


class Adjustment:
    def __init__(self, reason: str, identifier: str, amount: float):
        self.reason: str = reason
        self.identifier: str = identifier.strip()
        self.amount: float = round(amount, 2)
        self.numbers_for_notes: str = identifier
        self.validate_identifier()

    def __str__(self):
        return f'{self.reason} | {self.identifier} | {self.amount}'

    def validate_identifier(self):
        try:
            identifier_split: list = self.identifier.split()
            if re.findall(r'\d{4}-\d{2}-\d{2}', self.identifier):
                # EDY1NVNBG0000-12703188-2020-12-22
                self.numbers_for_notes = self.identifier.split('-')[0] + '-' + self.identifier.split('-')[1]
                self.identifier = self.identifier.split('-')[1]
            elif len(identifier_split) == 2:
                # 20200303 9062167
                if identifier_split[-1].startswith('/'):
                    self.identifier = identifier_split[0][1:]
                else:
                    self.identifier = identifier_split[-1]
            elif len(identifier_split) == 3:
                self.identifier = identifier_split[0]
            else:
                # 5203290000411957321 - last 8 number is claim ID
                self.identifier = self.identifier[-8:]
        except Exception as ex:
            log_message('Adjustment class: ' + str(ex))


class ACNT:
    def __init__(self, acnt_number: str):
        self.acnt_number: str = acnt_number
        self.icn_number: str = ''
        # list of Service() class
        self.services: list = []

    def __str__(self):
        return f'ACNT: {self.acnt_number}. ICN: {self.icn_number}'


class Service:
    def __init__(self, code: str, date: datetime, billed: float, allowed: float, prov_pd: float, obligations: dict):
        self.code: str = code
        if date is None:
            self.date: datetime = datetime.date.today()
        else:
            self.date: datetime = date

        self.billed: float = round(billed, 2)
        self.allowed: float = round(allowed, 2)
        self.prov_pd: float = round(prov_pd, 2)
        self.obligations: dict = obligations
        self.populated: bool = False

    def __str__(self):
        return f'{self.code} | billed: {self.billed} | allowed: {self.allowed} | prov_pd: {self.prov_pd}'
