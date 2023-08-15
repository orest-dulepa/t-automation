import fitz
import re
import datetime
import os
from libraries.eob import EOB, Adjustment, ACNT, Service


class PDF:
    def __init__(self):
        self.init = ''

    @staticmethod
    def read_pdf(path_to_pdf: str) -> str:
        text: str = ""
        with fitz.Document(path_to_pdf) as doc:
            for page in doc:
                text += page.getText()

        return text

    @staticmethod
    def get_list_of_service_dates(lines: list) -> list:
        list_of_service_dates: list = []
        current_position: int = 0
        while current_position < len(lines):
            line: str = str(lines[current_position]).strip()
            line_array: list = line.split()

            if len(line_array) >= 2 and line_array[0].isdigit() and line_array[1].startswith(line_array[0].strip()):
                list_of_service_dates.append(line)
            current_position += 1
        return list_of_service_dates

    def parse_eob_from_waystar(self, text: str, lines: list) -> (EOB, dict):
        insurance: str = str(lines[0]).strip()
        if 'llc' in insurance:
            insurance = str(lines[1]).strip()

        eob_data: EOB = EOB()
        eob_data.insurance_name = insurance
        acnt_data: dict = {}

        list_of_service_dates: list = self.get_list_of_service_dates(lines)
        current_position: int = 0
        current_acnt: ACNT = ACNT('')
        while current_position < len(lines):
            line: str = str(lines[current_position]).strip()
            line_array: list = line.split()

            if 'EFT:' in line or 'CHECK NUM:' in line:
                eft_number = lines[current_position + 1]
                eob_data.eft_number = eft_number
                current_position += 1
                continue

            if 'CHECK DATE:' in line:
                eob_data.date = datetime.datetime.strptime(lines[current_position + 1], '%m/%d/%Y')
                current_position += 1
                continue

            if line.startswith('ACNT:'):
                if current_acnt.acnt_number:
                    # print(current_acnt)
                    if current_acnt.acnt_number not in acnt_data:
                        acnt_data[current_acnt.acnt_number]: ACNT = current_acnt
                    else:
                        acnt_data[current_acnt.acnt_number].services += current_acnt.services
                acnt_number: str = line.split(':')[-1]
                current_position += 1
                current_acnt = ACNT(acnt_number)
                continue

            if line.startswith('ICN:'):
                icn_number: str = line.split(':')[-1]
                current_acnt.icn_number = icn_number
                current_position += 1
                continue

            if line.startswith('PROVIDER ADJ DETAILS'):
                while str(lines[current_position]).strip() != 'AMOUNT':
                    current_position += 1
                current_position += 1
                while not str(lines[current_position]).strip().startswith('GLOSSARY:') and 'PAGE' not in str(lines[current_position]).upper():
                    reason_code: str = str(lines[current_position]).strip().upper()
                    identifier: str = str(lines[current_position + 1]).strip()
                    amount: str = str(lines[current_position + 2]).strip().replace(',', '')
                    if re.findall(r'\d+\.\d{2}', identifier):
                        amount = identifier
                        identifier = ''
                        current_position -= 1
                    # print(reason_code, identifier, amount, current_position)
                    # Add only if required adjustment
                    if reason_code in ['WO', 'FB', 'L6']:
                        eob_data.adjustments.append(Adjustment(reason_code, identifier, float(amount)))
                    current_position += 3
                break

            if len(line_array) >= 2 and line_array[0].isdigit() and line_array[1].startswith(line_array[0].strip()):
                new_position: int = current_position + 1

                temp_str: str = str(lines[new_position]).strip().upper()
                while len(temp_str) != 5 and ':' not in temp_str or '.' in temp_str:
                    temp_list: list = temp_str.split()
                    if len(temp_list) == 2 and len(temp_list[0]) == 5 and ':' not in temp_list[0]:
                        temp_str = temp_list[0]
                        break
                    if (len(temp_list) == 3 or len(temp_list) == 4) and len(temp_list[2]) == 5:
                        temp_str = temp_list[2]
                        break
                    if re.findall(r'(\w\d{3}\w)(\w{2}(\w{2}|))', temp_str):
                        temp_str = re.findall(r'(\w\d{3}\w)(\w{2}(\w{2}|))', temp_str)[0][0]
                        break
                    new_position += 1
                    temp_str: str = str(lines[new_position]).strip().upper()
                cpt_code: str = temp_str
                if len(cpt_code) != 5 or '.' in cpt_code:
                    current_acnt.acnt_number = ''
                    current_position += 1
                    continue

                check_mod = re.search(r'\d+\.\d{2}', str(lines[new_position + 1]).strip())
                if check_mod is None:
                    new_position += 1

                billed: str = ''
                allowed: str = ''
                prov_pd: str = ''
                obligation_amount: str = '0.0'
                obligations: dict = {}
                is_obligations: bool = False

                current_position = new_position
                count: int = 0
                while True:
                    new_position += 1
                    if new_position == len(lines) or str(lines[new_position]).strip() in list_of_service_dates:
                        # print('000', new_position)
                        # print(current_acnt.acnt_number)
                        # print(cpt_code)
                        # print(obligations)
                        if not obligations and float(obligation_amount) > .0:
                            obligations = {
                                'PR': float(obligation_amount)
                            }
                        current_acnt.services.append(
                            Service(
                                cpt_code,
                                None,
                                float(billed),
                                float(allowed),
                                float(prov_pd),
                                obligations
                            )
                        )
                        break
                    check_amount = re.search(r'(-|)\d+\.\d{2}', str(lines[new_position]).strip())
                    check_obligation_code = re.search(r'([a-zA-Z]{2}-\w+)', str(lines[new_position]).strip())
                    if check_obligation_code is not None:
                        is_obligations = True
                        obligation_code: str = check_obligation_code[0]
                        if check_amount is not None:
                            count += 1
                        if re.search(r'(PR-\w+|PI-\w+|OA-\w+|CR-\w+)', obligation_code) is not None:
                            temp_count: int = 2
                            if check_amount is not None:
                                obligation_amount: str = check_amount[0]
                                temp_count = 1
                            else:
                                obligation_amount: str = str(lines[new_position + 1]).split()[0]

                            if not prov_pd:
                                prov_pd = str(lines[new_position + temp_count]).strip().upper()
                            # print('333', obligation_code, obligation_amount)
                            obligations[obligation_code] = round(float(obligation_amount), 2)
                        continue

                    count += 1
                    if count == 1:
                        billed = str(lines[new_position]).strip()

                        check_billed: list = billed.split()
                        if len(check_billed) == 2:
                            billed = check_billed[0]
                            allowed = check_billed[1]
                            count += 1
                        elif len(check_billed) == 3:
                            billed = check_billed[0]
                            allowed = check_billed[1]
                            count += 2
                    elif count == 2:
                        allowed = str(lines[new_position]).strip()

                        check_allowed: list = allowed.split()
                        if len(check_allowed) == 2:
                            allowed = check_allowed[0]
                            count += 1
                        elif len(check_allowed) == 3:
                            allowed = check_allowed[0]
                            obligation_amount = check_allowed[2]
                            count += 2
                        elif re.findall(r'((-|)\d+\.\d{2})((-|)\d+\.\d{2})', allowed):
                            allowed = re.findall(r'((-|)\d+\.\d{2})((-|)\d+\.\d{2})', allowed)[0][0]
                            count += 1
                    elif count == 3:
                        check_3: list = str(lines[new_position]).strip().split()
                        if len(check_3) == 2:
                            obligation_amount = check_3[1]
                            count += 1
                        elif re.findall(r'((-|)\d+\.\d{2})((-|)\d+\.\d{2})', str(lines[new_position]).strip()):
                            obligation_amount = re.findall(r'((-|)\d+\.\d{2})((-|)\d+\.\d{2})', str(lines[new_position]).strip())[0][2]
                            count += 1
                    elif count == 4 and 'Patient Responsibility' in text and not obligation_amount:
                        obligation_amount = str(lines[new_position]).strip()
                    elif count == 5:
                        check_5: list = str(lines[new_position]).strip().split()
                        if len(check_5) == 2:
                            prov_pd = check_5[1]
                            count += 1
                        elif not is_obligations:
                            prov_pd = check_5[0]
                    elif count == 6 and not prov_pd:
                        prov_pd = str(lines[new_position]).strip()
                        check_prov_pd: list = str(lines[new_position]).strip().split()
                        if len(check_prov_pd) == 2:
                            prov_pd = check_prov_pd[0]

            current_position += 1
        if current_acnt.acnt_number and current_acnt.acnt_number not in acnt_data:
            acnt_data[current_acnt.acnt_number] = current_acnt
        elif current_acnt.acnt_number:
            acnt_data[current_acnt.acnt_number].services += current_acnt.services
        return eob_data, acnt_data

    @staticmethod
    def to_float(text: str) -> float:
        return float(text.replace('$', '').replace(',', ''))

    def parse_humana(self, text: str, lines: list) -> (EOB, dict):
        eob_data: EOB = EOB()
        acnt_data: dict = {}

        current_position: int = 0
        current_acnt: ACNT = ACNT('')
        while current_position < len(lines):
            line: str = str(lines[current_position]).strip()

            if not eob_data.insurance_name and 'Payer:' in line:
                eob_data.insurance_name = line.split(':')[-1].strip()
                current_position += 1
                # print(eob_data.insurance_name)
                continue
            if not eob_data.eft_number and 'Check/EFT Trace Number:' in line:
                eob_data.eft_number = line.split(':')[-1].strip()
                current_position += 1
                # print(eob_data.eft_number)
                continue

            if 'Patient Ctrl Nmbr:' in line:
                if current_acnt.acnt_number:
                    acnt_data[current_acnt.acnt_number] = current_acnt
                claim_number: str = str(line.split(':')[-1]).strip()
                # print(claim_number)
                current_acnt: ACNT = ACNT(claim_number)

            if line.endswith('Payment'):
                date_of_service: str = ''
                cpt_code: str = ''
                obligations_list: list = []
                obligations: dict = {}
                allowed: str = ''
                billed: str = ''

                count_of_dollar: int = 0
                while line != 'Patient Name':
                    current_position += 1
                    line: str = str(lines[current_position]).strip()
                    if 'Patient Name' in line or 'Code Descriptions' in line or 'Line Details' in line or (line.isdigit() and count_of_dollar > 2):
                        prov_pd: str = str(lines[current_position - 1]).strip()
                        for code in obligations_list:
                            is_valid_code: bool = False
                            for allowed_code in ['PR', 'PI', 'OA', 'CR']:
                                if allowed_code in code:
                                    is_valid_code = True
                            if not is_valid_code:
                                obligations.pop(code)
                        # Add to current ACNT
                        current_acnt.services.append(
                            Service(
                                cpt_code,
                                None,
                                self.to_float(billed),
                                self.to_float(allowed),
                                self.to_float(prov_pd),
                                obligations
                            )
                        )

                        date_of_service: str = ''
                        cpt_code: str = ''
                        obligations_list: list = []
                        obligations: dict = {}
                        allowed: str = ''
                        billed: str = ''
                        break

                    if not date_of_service and re.findall(r'\d{2}/\d{2}/\d{4}', line):
                        date_of_service = re.findall(r'\d{2}/\d{2}/\d{4}', line)[0]
                        continue

                    if re.findall(r'\S{2}:\S{5}', line):
                        cpt_code = re.findall(r'\S{2}:\S{5}', line)[0]
                        cpt_code = cpt_code.split(':')[-1]
                        continue

                    if '$' in line:
                        count_of_dollar += 1

                        if count_of_dollar == 1:
                            allowed: str = line.split()[0]
                        elif count_of_dollar == 2:
                            billed: str = line.split()[0]

                    if re.findall(r'\w{2}-\d+', line):
                        obligation_code: str = re.findall(r'\w{2}-\d+', line)[0]
                        obligations_list.append(obligation_code)

                        obligations[obligation_code] = ''
                        if '$' in line.split()[-1]:
                            obligations[obligation_code] = self.to_float(line)
                            continue
                        # try find amount
                        obligation_dollar: int = 0
                        new_position: int = 0
                        while not obligations[obligation_code]:
                            new_position += 1
                            line: str = str(lines[current_position + new_position]).strip()
                            if '$' in line:
                                obligation_dollar += 1
                                if obligation_dollar == len(obligations_list):
                                    obligations[obligation_code] = self.to_float(line)
                                    break
                        count_of_dollar += 1
            current_position += 1
        if current_acnt.acnt_number and current_acnt.acnt_number not in acnt_data:
            acnt_data[current_acnt.acnt_number] = current_acnt
        return eob_data, acnt_data

    def parse_tricare(self, text: str, lines: list) -> (EOB, dict):
        eob_data: EOB = EOB()
        acnt_data: dict = {}

        current_position: int = 0
        current_acnt: ACNT = ACNT('')
        while current_position < len(lines):
            line: str = str(lines[current_position]).strip()
            line_array: list = line.split()

            if not eob_data.insurance_name and 'Keep this notice for your records' in line:
                eob_data.insurance_name = line.split()[0].strip()
                current_position += 1
                # print(eob_data.insurance_name)
                continue
            if not eob_data.eft_number and 'Check Number:' in line:
                eob_data.eft_number = line.split(':')[-1].strip()
                current_position += 1
                # print(eob_data.eft_number)
                continue

            if 'Patient Number:' in line:
                if current_acnt.acnt_number:
                    acnt_data[current_acnt.acnt_number] = current_acnt
                claim_number: str = str(line.split(':')[-1]).strip()
                # print(claim_number)
                current_acnt: ACNT = ACNT(claim_number)

                date_of_service: str = ''
                cpt_code: str = ''
                pr_amount: float = 0.0
                obligations: dict = {}
                allowed: str = ''
                billed: str = ''
                prov_pd: str = ''

                count_of_dollar: int = 0
                while 'Claim Totals' not in line:
                    current_position += 1
                    line: str = str(lines[current_position]).strip()

                    if not date_of_service and re.findall(r'\d{2}/\d{2}/\d{2}', line):
                        date_of_service = re.findall(r'\d{2}/\d{2}/\d{2}', line)[0]
                        continue
                    if date_of_service and re.findall(r'(\S{5}) \d+', line):
                        cpt_code = re.findall(r'(\S{5}) \d+', line)[0]

                    if '$' in line:
                        count_of_dollar += 1
                        if count_of_dollar == 1:
                            billed = line
                        elif count_of_dollar == 2:
                            allowed = line
                        elif count_of_dollar == 3 or count_of_dollar == 4:
                            pr_amount += self.to_float(line)
                        elif count_of_dollar == 5:
                            prov_pd = line

                    if prov_pd:
                        if pr_amount > 0.0:
                            obligations['PR'] = pr_amount
                        current_acnt.services.append(
                            Service(
                                cpt_code,
                                datetime.datetime.strptime(date_of_service, '%m/%d/%y'),
                                self.to_float(billed),
                                self.to_float(allowed),
                                self.to_float(prov_pd),
                                obligations
                            )
                        )
                        date_of_service: str = ''
                        cpt_code: str = ''
                        pr_amount: float = 0.0
                        obligations: dict = {}
                        allowed: str = ''
                        billed: str = ''
                        prov_pd: str = ''
            current_position += 1
        if current_acnt.acnt_number and current_acnt.acnt_number not in acnt_data:
            acnt_data[current_acnt.acnt_number] = current_acnt
        return eob_data, acnt_data

    def parse_beacon_health_options(self, text: str, lines: list) -> (EOB, dict):
        eob_data: EOB = EOB()
        acnt_data: dict = {}

        current_position: int = 0
        current_acnt: ACNT = ACNT('')
        while current_position < len(lines):
            line: str = str(lines[current_position]).strip()

            if not eob_data.insurance_name and 'Profile:' in line:
                temp_insurance: str = str(lines[current_position + 1]).strip()
                eob_data.insurance_name = temp_insurance.split(',')[0]
                current_position += 2
                # print(eob_data.insurance_name)
                continue
            if not eob_data.eft_number and 'Check #:' in line:
                eob_data.eft_number = line.split(':')[-1].strip()
                current_position += 1
                # print(eob_data.eft_number)
                continue

            if 'Claim #:' in line:
                if current_acnt.acnt_number:
                    acnt_data[current_acnt.acnt_number] = current_acnt
                temp_claim_number: str = str(lines[current_position - 1]).strip()
                claim_number: str = temp_claim_number.split(':')[-1].strip()
                # print(claim_number)
                current_acnt: ACNT = ACNT(claim_number)

                date_of_service: str = ''
                cpt_code: str = ''
                pr_amount: float = 0.0
                obligations: dict = {}
                allowed: str = ''
                billed: str = ''
                prov_pd: str = ''

                count_of_dollar: int = 0
                while 'Claim Totals' not in line:
                    current_position += 1
                    line: str = str(lines[current_position]).strip()

                    if not date_of_service and re.findall(r'\d{2}/\d{2}/\d{4}', line):
                        date_of_service = re.findall(r'\d{2}/\d{2}/\d{4}', line)[0]
                    if date_of_service and not cpt_code and len(line) == 5:
                        cpt_code = line
                        count_of_dollar: int = 0

                    if re.findall(r'\d+\.\d{2}', line):
                        count_of_dollar += 1

                        if count_of_dollar == 1:
                            billed = line
                        elif count_of_dollar == 2:
                            allowed = line
                        elif count_of_dollar == 3 or count_of_dollar == 4:
                            pass  # Provider Withhold and Discount Amount
                        elif count_of_dollar == 8 or count_of_dollar == 9 or count_of_dollar == 10:
                            pr_amount += self.to_float(line)
                        elif count_of_dollar == 11:
                            prov_pd = line

                    if prov_pd:
                        if pr_amount > 0.0:
                            obligations['PR'] = pr_amount
                        current_acnt.services.append(
                            Service(
                                cpt_code,
                                datetime.datetime.strptime(date_of_service, '%m/%d/%Y'),
                                self.to_float(billed),
                                self.to_float(allowed),
                                self.to_float(prov_pd),
                                obligations
                            )
                        )
                        date_of_service: str = ''
                        cpt_code: str = ''
                        pr_amount: float = 0.0
                        obligations: dict = {}
                        allowed: str = ''
                        billed: str = ''
                        prov_pd: str = ''
            current_position += 1
        if current_acnt.acnt_number and current_acnt.acnt_number not in acnt_data:
            acnt_data[current_acnt.acnt_number] = current_acnt
        return eob_data, acnt_data

    def parse_eob(self, path_to_pdf: str) -> (EOB, dict):
        text: str = self.read_pdf(path_to_pdf)
        lines: list = text.split('\n')

        eob_data: EOB = EOB()
        acnt_data: dict = {}
        try:
            if lines[0] == 'Check Summary':
                eob_data, acnt_data = self.parse_humana(text, lines)
            elif 'Address Page' in text:
                eob_data, acnt_data = self.parse_tricare(text, lines)
            elif 'PROVIDER SUMMARY VOUCHER' in text:
                eob_data, acnt_data = self.parse_beacon_health_options(text, lines)
            else:
                eob_data, acnt_data = self.parse_eob_from_waystar(text, lines)

            if 'denied' in text.lower():
                eob_data.denial = True
                for i in range(len(lines)):
                    current_line: str = lines[-i]
                    if 'denied' in current_line.lower():
                        eob_data.denial_code = lines[-i - 1]
                        break

            print('Original insurance name: ' + eob_data.insurance_name)
            if 'INSURANCE COMPANY' in eob_data.insurance_name:
                eob_data.insurance_name = eob_data.insurance_name.replace('INSURANCE COMPANY', '').strip()
            if 'CORPORATION' in eob_data.insurance_name:
                eob_data.insurance_name = eob_data.insurance_name.replace('CORPORATION', '').strip()
            if 'INC.' in eob_data.insurance_name:
                eob_data.insurance_name = eob_data.insurance_name.replace('INC.', '').strip()
            if 'CIGNA' in eob_data.insurance_name:
                eob_data.insurance_name = 'CIGNA'
            if 'UNITED HEALTHCARE' in eob_data.insurance_name:
                eob_data.insurance_name = 'United Behavioral Healthcare'
            if ' AND ' in eob_data.insurance_name:
                eob_data.insurance_name = eob_data.insurance_name.replace(' AND ', ' ').strip()
            if 'UNITED HEALTHCARE' in eob_data.insurance_name:
                eob_data.insurance_name = 'United Behavioral Healthcare'
            if 'BCBS' in eob_data.insurance_name:
                eob_data.insurance_name = 'Blue Cross Blue Shield'
            eob_data.insurance_name = eob_data.insurance_name.strip(',')
            print(eob_data.insurance_name)
        except Exception as ex:
            # raise ex
            print(str(ex))
            print(path_to_pdf)

            eob_data: EOB = EOB()
            acnt_data: dict = {}

        return eob_data, acnt_data


def local_test():
    pdf: PDF = PDF()
    eob_data, acnt_data = pdf.parse_eob(r'C:\Users\Serhii\Desktop\ViewEOB (2).pdf')

    print(eob_data)
    print(acnt_data)
    print('end')


if __name__ == '__main__':
    local_test()
