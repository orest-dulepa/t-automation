import re
from datetime import datetime


class InvoiceData:
    def __init__(self):
        self.case: str = ''
        self.full_name: str = ''
        self.first_name: str = ''
        self.last_name: str = ''
        self.amount: str = ''
        self.last4digits: str = ''
        self.last4digits_1: str = ''
        self.check_owner: str = ''
        self.trustee_full_name: str = ''
        self.trustee_last_name: str = ''
        self.trustee_state: str = ''
        self.claim: str = ''

        self.secondary_debtor: str = ''
        self.secondary_debtor_last_name: str = ''

        self.check_number: str = ''
        self.check_date: str = ''

        self.lci_id: str = ''
        self.portfolio_id: str = ''
        self.true_owner: str = ''
        self.servicing_fee: str = ''
        self.putbacks: str = ''

    def __str__(self):
        result: str = ''
        result += f'Case: {self.case}\n'
        result += f'Debtor name: {self.full_name}\n'
        result += f'Account (4 digit): {self.last4digits}, {self.last4digits_1}\n'
        result += f'Amount: {self.amount}\n'

        result += f'Trustee: {self.trustee_full_name}, {self.trustee_state}\n'

        result += f'Owner: {self.check_owner}\n'
        result += f'Check number: {self.check_number}, check date: {self.check_date}\n'
        result += f'Claim: {self.claim}\n'

        result += f'LCI_ID: {self.lci_id}\n'
        result += f'Portfolio_ID{self.portfolio_id}\n'

        return result

    def prepare_data(self):
        if re.findall(r'(\d{2}-\d+) [a-zA-Z]{3} ', self.case):
            self.case = re.findall(r'(\d{2}-\d+) [a-zA-Z]{3} ', self.case)[0]

        self.case = self.case.replace(' ', '')
        if 'Comment' in self.full_name:
            self.full_name = self.full_name.split('Comment')[0].strip()

        self.full_name = self.full_name.strip()
        try:
            if ',' in self.full_name:
                temp_name: list = self.full_name.split()
                if len(temp_name) >= 2:
                    self.first_name = temp_name[1].strip()
                self.last_name = temp_name[0].strip()
            else:
                temp_name: list = self.full_name.split()
                self.first_name = temp_name[0].strip()
                self.last_name = temp_name[-1].strip()
        except:
            pass
        self.first_name.strip('.').strip(',')
        self.last_name.strip('.').strip(',')

        if self.trustee_full_name:
            self.trustee_last_name = self.trustee_full_name.split()[-1].strip()
            self.trustee_last_name.strip('.').strip(',')
        if self.trustee_last_name.isdigit():
            self.trustee_last_name = ''

        if re.findall(r'(.*) P(.| |)O(.| |) ', self.check_owner, re.I):
            self.check_owner = re.findall(r'(.*) P(.| |)O(.| |) ', self.check_owner, re.I)[0][0]
        if 'P.O.' in self.check_owner:
            self.check_owner = self.check_owner.split('P.O.')[0]
        if self.check_owner.startswith('.7'):
            self.check_owner = '13/7, LLC'
        elif self.check_owner.startswith('/7'):
            self.check_owner = '13/7, LLC'
        elif '13.7' in self.check_owner:
            self.check_owner = self.check_owner.replace('13.7', '13/7')
        if '13/7' == self.check_owner:
            self.check_owner = self.check_owner + ', LLC'
        # fix LLC and Inc issue
        if ' LLC' in self.check_owner and ', LLC' not in self.check_owner:
            self.check_owner = self.check_owner.replace(' LLC', ', LLC')
        if ' Inc' in self.check_owner and ', Inc' not in self.check_owner:
            self.check_owner = self.check_owner.replace(' Inc', ', Inc')

        if self.case.count('-') > 1:
            temp_case = self.case.split('-')
            self.case = f'{temp_case[0]}-{temp_case[1]}'

        if not self.claim and '[' in self.last4digits:
            if re.findall(r'\[([0-9]+)', self.last4digits):
                self.claim = re.findall(r'\[([0-9]+)', self.last4digits)[0]
        if re.findall(r'([0-9]+)', self.claim):
            self.claim = re.findall(r'([0-9]+)', self.claim)[0]
        self.claim = self.claim.lstrip('0')
        if re.findall(r'([0-9]+)', self.last4digits):
            self.last4digits = re.findall(r'([0-9]+)', self.last4digits)[0]

        try:
            temp_date = datetime.strptime(self.check_date, '%b %d, %Y')
            self.check_date = temp_date.strftime('%m/%d/%Y')
        except:
            pass
