import boto3
import time
import os
import re
from datetime import datetime
from libraries.invoice import InvoiceData


class TextractParsing:
    def __init__(self, pdf_file_path, bucket_name: str):
        self.bucket_name = bucket_name
        self.pdf_file_path: str = pdf_file_path
        self.pdf_base_name: str = os.path.basename(pdf_file_path)
        self.pdf_s3_file_name: str = datetime.utcnow().strftime('%m-%d-%Y_%H-%M-%S-%f_') + self.pdf_base_name

        self.blocks: list = []
        self.raw_text: list = []

    def upload_file_to_s3(self):
        # Upload PDF to S3
        s3 = boto3.client('s3')
        s3.upload_file(self.pdf_file_path, self.bucket_name, self.pdf_s3_file_name)

    def get_response_from_textract(self):
        textract = boto3.client('textract')
        response = textract.start_document_analysis(
            DocumentLocation={'S3Object': {'Bucket': self.bucket_name, 'Name': self.pdf_s3_file_name}},
            FeatureTypes=['TABLES', 'FORMS']
        )

        job_id: str = response['JobId']
        print(f'Job ID {job_id}')
        for i in range(50):
            time.sleep(2)
            response = textract.get_document_analysis(JobId=job_id)
            if response['JobStatus'] != 'IN_PROGRESS':
                print(f"Job status {response['JobStatus']}")
                break

        self.blocks = response['Blocks']

    @staticmethod
    def get_text(result, blocks_map) -> str:
        text: str = ''

        if 'Relationships' in result:
            for relationship in result['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        word = blocks_map[child_id]
                        if word['BlockType'] == 'WORD':
                            text += word['Text'] + ' '
                        if word['BlockType'] == 'SELECTION_ELEMENT':
                            if word['SelectionStatus'] == 'SELECTED':
                                text += 'X '
        return text

    def get_rows_columns_map(self, table_info, blocks_map) -> dict:
        rows: dict = {}

        for relationship in table_info['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    if child_id in blocks_map:
                        cell = blocks_map[child_id]
                        if cell['BlockType'] == 'CELL':
                            row_index = cell['RowIndex']
                            col_index = cell['ColumnIndex']
                            if row_index not in rows:
                                rows[row_index] = {}
                            rows[row_index][col_index] = self.get_text(cell, blocks_map)
        return rows

    def generate_table(self, table_info, blocks_map) -> list:
        rows = self.get_rows_columns_map(table_info, blocks_map)

        table: list = []
        for row_index, cols in rows.items():
            row_data: list = []
            for col_index, text in cols.items():
                row_data.append(str(text).strip())
            table.append(row_data)

        return table

    def get_table_results(self, blocks: list) -> list or str:
        blocks_map: dict = {}
        table_blocks: list = []

        for block in blocks:
            blocks_map[block['Id']] = block
            if block['BlockType'] == "TABLE":
                table_blocks.append(block)

        if len(table_blocks) <= 0:
            return 'No Table found'

        result_table: list = []
        for index, table_info in enumerate(table_blocks):
            result_table += self.generate_table(table_info, blocks_map)

        return result_table

    def get_key_value_pair(self, blocks: list) -> dict:
        key_map, value_map, block_map = self.get_kv_map(blocks)
        key_value_pair = self.get_kv_relationship(key_map, value_map, block_map)

        return key_value_pair

    @staticmethod
    def get_kv_map(blocks: list):
        key_map = {}
        value_map = {}
        block_map = {}

        for block in blocks:
            block_id = block['Id']
            block_map[block_id] = block
            if block['BlockType'] == "KEY_VALUE_SET":
                if 'KEY' in block['EntityTypes']:
                    key_map[block_id] = block
                else:
                    value_map[block_id] = block

        return key_map, value_map, block_map

    def get_kv_relationship(self, key_map, value_map, block_map):
        kvs = {}

        for block_id, key_block in key_map.items():
            value_block = self.find_value_block(key_block, value_map)
            key = self.get_text(key_block, block_map)
            val = self.get_text(value_block, block_map)
            kvs[key.strip()] = val.strip()

        return kvs

    @staticmethod
    def find_value_block(key_block, value_map):
        value_block = {}

        for relationship in key_block['Relationships']:
            if relationship['Type'] == 'VALUE':
                for value_id in relationship['Ids']:
                    if value_id in value_map:
                        value_block = value_map[value_id]

        return value_block

    @staticmethod
    def find_header_row(table: list) -> int:
        for row in table:
            for col in row:
                if 'case' in col.lower():
                    return table.index(row)
        return -1

    @staticmethod
    def get_column_index(header_row: list, column_name: str) -> int:
        for header in header_row:
            if column_name.strip().lower() in header.lower():
                return header_row.index(header)
        return -1

    def get_column_data(self, current_row: list, header_row: list, column_name: str) -> str:
        value: str = ''

        index: int = self.get_column_index(header_row, column_name)
        if index >= 0:
            value = current_row[index]
        return value.strip()

    def get_raw_text(self):
        self.raw_text = []
        for item in self.blocks:
            if item["BlockType"] == "LINE":
                self.raw_text.append(item["Text"])

    def prepare_result(self):
        self.get_raw_text()
        table = self.get_table_results(self.blocks)
        key_value_pair: dict = self.get_key_value_pair(self.blocks)

        list_of_items: list = []

        trustee_full_name: str = ''
        check_owner: str = ''
        check_date: str = ''
        check_number: str = ''
        last4digits: str = ''
        for key, value in key_value_pair.items():
            key_lower: str = key.lower()

            if 'TO THE ORDER OF'.lower() in key_lower and not check_owner:
                check_owner = str(value.split('PO BOX')[0]).strip()
                if re.findall(r'^\d+', check_owner):
                    check_owner = check_owner.replace(re.findall(r'^\d+', check_owner)[0], '')
            elif 'TO THE FOLLOWING'.lower() in key_lower and not check_owner:
                check_owner = value
            if 'date' in key_lower and not check_date:
                if not value.replace('.', '').replace(',', '').isdigit():
                    check_date = value
            if 'check' in key_lower and 'amount' not in key_lower and not check_number:
                check_number = value
            if 'no.' == key_lower and not check_number:
                check_number = value
            if 'ACCT'.lower() in key_lower and not last4digits and value:
                last4digits = str(value.split()[0]).strip()
            if 'ACCT'.lower() in value.lower() and not last4digits:
                last4digits = str(value.split()[-1]).strip('*')
            if 'CHAPTER 13 TRUSTEE'.lower() in key_lower and not trustee_full_name:
                if re.findall(r'(.+) CHAPTER 13 TRUSTEE', key, re.I):
                    trustee_full_name = re.findall(r'(.+) CHAPTER 13 TRUSTEE', key, re.I)[0]
            if 'CHAPTER 13 TRUSTEE' == value and not trustee_full_name:
                trustee_full_name = key

        trustee_state: str = ''
        claim: str = ''
        position: int = 0
        trustee_validation: int = 0
        while position < len(self.raw_text):
            line: str = self.raw_text[position].lower()

            if 'TRUSTEE'.lower() in line and not trustee_full_name:
                trustee_full_name = self.raw_text[position - 1]

                if len(trustee_full_name) == 1:
                    trustee_validation = 1
                    if 'CHAPTER 13 TRUSTEE' not in self.raw_text[position + 1]:
                        trustee_full_name = self.raw_text[position + 1]
                        position += 1
                        continue
                elif len(trustee_full_name) == 2:
                    trustee_full_name = self.raw_text[position]
                if type(table) == str and ', trustee' in line:
                    trustee_full_name = self.raw_text[position]
                if 'PRESTEE' == trustee_full_name.upper():
                    trustee_full_name = self.raw_text[0]
                if 'watermark' in trustee_full_name.lower() or 'CHECK NUMBER'.lower() in trustee_full_name.lower():
                    if re.findall(r'(.*)TRUSTEE', self.raw_text[position], re.I):
                        trustee_full_name = re.findall(r'(.*)TRUSTEE', self.raw_text[position], re.I)[0].strip()
                        if not trustee_full_name:
                            trustee_full_name = self.raw_text[position + 3]
                    if 'CHAPTER 13'.lower() == trustee_full_name.lower():
                        trustee_full_name = self.raw_text[0]
                if 'OFFICE OF THE CHAPTER 13 TRUSTEE'.lower() in line or 'CHECK PRINTED'.lower() in line:
                    if re.findall(r'(.*)TRUSTEE', self.raw_text[position + 1], re.I) and trustee_validation != 1:
                        trustee_full_name = re.findall(r'(.*)TRUSTEE', self.raw_text[position + 1], re.I)[0].strip()
                    if 'WARNING' in line.upper() or 'WARNING' in trustee_full_name.upper():
                        trustee_full_name = self.raw_text[position + 2]
                        if trustee_full_name.isdigit():
                            trustee_full_name = self.raw_text[position + 1]
                        elif trustee_full_name.replace('-', '').isdigit():
                            trustee_full_name = self.raw_text[position + 3]
                        if 'PREMIUM' == trustee_full_name:
                            trustee_full_name = self.raw_text[position + 5]
                        if trustee_full_name.replace('-', '').isdigit():
                            trustee_full_name = self.raw_text[position + 4]
                        if trustee_full_name == '$':
                            position += 1
                            trustee_validation = 2
                            trustee_full_name = ''
                    if 'CHAPTER 13 STANDING' in trustee_full_name:
                        trustee_full_name = trustee_full_name.replace('CHAPTER 13 STANDING', '').strip()
                    elif 'CHAPTER 13'.lower() in trustee_full_name.lower():
                        trustee_full_name = trustee_full_name.split(',')[0]
                        if 'CHAPTER 13'.lower() in trustee_full_name.lower():
                            trustee_full_name = self.raw_text[position + 5]
                    position += 1
                    continue
                if line.endswith('TRUSTEE NAME'.lower()) or line.endswith('trustee mame'):
                    trustee_full_name = self.raw_text[position + 1]
                if trustee_full_name.isdigit():
                    trustee_full_name = self.raw_text[position + 1]
                    if trustee_full_name.isdigit():
                        trustee_full_name = self.raw_text[position - 3]
                    elif trustee_full_name and trustee_full_name.split()[0].strip().isdigit():
                        trustee_full_name = self.raw_text[position - 4]
                if '-' in trustee_full_name:
                    trustee_full_name = self.raw_text[position - 2]
                    if 'CHECK NUMBER' == trustee_full_name:
                        trustee_full_name = self.raw_text[position - 4]
                if 'BANK' in trustee_full_name:
                    trustee_full_name = self.raw_text[position - 3]
                    if trustee_full_name.replace('-', '').isdigit():
                        trustee_full_name = self.raw_text[position - 4]
                if not check_number:
                    check_number = self.raw_text[position + 2]
                    if 'box' in check_number.lower():
                        check_number = self.raw_text[position - 1]
                    if type(table) == str and ', trustee' in line:
                        check_number = self.raw_text[position + 1]
                if trustee_full_name.replace(',', '').replace('.', '').isdigit():
                    trustee_full_name = self.raw_text[position + 3]
            if trustee_full_name and not trustee_state and position > 2:
                limit: int = 20
                while not re.search(r'( [a-zA-Z]{2} )', self.raw_text[position]) or ' OR ' in self.raw_text[position]:
                    if limit < 0 or position + 1 >= len(self.raw_text):
                        break
                    limit -= 1
                    position += 1
                if re.search(r'( [a-zA-Z]{2} )', self.raw_text[position]):
                    trustee_state = str(re.search(r'( [a-zA-Z]{2} )', self.raw_text[position])[0]).strip()
                position -= 20 - limit
            if 'claim' in line and not claim:
                if re.findall(r'([0-9]+)', self.raw_text[position]):
                    claim = re.findall(r'([0-9]+)', self.raw_text[position])[0]
            if not last4digits and 'creditor account' in line:
                if re.findall(r'creditor account #([0-9]{4})', self.raw_text[position]):
                    last4digits = re.findall(r'creditor account #([0-9]{4})', self.raw_text[position])[0]
            if not check_owner and 'payee:' in line:
                check_owner = self.raw_text[position].split(':')[-1].strip()
            if not check_number and 'check #' in line:
                check_number = self.raw_text[position + 1]
            if not check_date and 'DATE:'.lower() in line:
                check_date = self.raw_text[position + 1]
            position += 1
        if trustee_full_name:
            trustee_full_name = trustee_full_name.strip('.').strip(',')
            trustee_full_name = trustee_full_name.split(',')[0]

        if trustee_full_name.count('-') > 1:
            trustee_full_name = ''

        position: int = 0
        while position < len(self.raw_text):
            line: str = self.raw_text[position].lower()
            if 'ATTORNEY AT LAW'.lower() in line and not check_number:
                check_number = self.raw_text[position - 1]
            if not trustee_full_name and 'name' == line:
                trustee_full_name = self.raw_text[position + 1]
            position += 1

        index: int = self.find_header_row(table)
        if index >= 0:
            header_row: list = table[index]
            while index >= 0:
                table.remove(table[index])
                index -= 1

            for row in table:
                if len(row) < len(header_row):
                    continue
                item: InvoiceData = InvoiceData()
                item.case = self.get_column_data(row, header_row, 'case')
                if item.case.lower() == 'case number':
                    continue

                if not item.case:
                    if list_of_items:
                        item = list_of_items[-1]
                        for col in row:
                            col_lower: str = col.lower()
                            if (not item.last4digits or item.last4digits == last4digits) and 'acct:' in col_lower:
                                item.last4digits = col_lower.split('acct:')[-1].strip()
                            elif not item.last4digits:
                                temp_acc = self.get_column_data(row, header_row, 'Account')
                                if temp_acc:
                                    item.last4digits = temp_acc.split()[0].strip()
                            if not item.claim and 'clm#' in col_lower:
                                temp_value = col_lower.split(':')[-1]
                                item.claim = temp_value.split('/')[0]
                            if not item.claim and '[' in col_lower and ']' in col_lower:
                                if re.findall(r'\[(\d+)', col_lower):
                                    item.claim = re.findall(r'\[(\d+)', col_lower)[0]
                            if not item.full_name:
                                debtor = self.get_column_data(row, header_row, 'collateral description')
                                if 'Debtor(s):' in debtor:
                                    item.full_name = debtor.split('Debtor(s):')[-1].strip()
                            if not item.full_name:
                                debtor_and_acct = self.get_column_data(row, header_row, 'Clm # Acct #')
                                if 'Debtor' in debtor_and_acct:
                                    item.full_name = re.findall(r'Debtor\D*:(.+)', debtor_and_acct, re.I)[0].strip()
                                    if re.findall(r'(\d{4}) Debtor\D*:', debtor_and_acct, re.I):
                                        item.last4digits = re.findall(r'(\d{4}) Debtor\D*:', debtor_and_acct, re.I)[0].strip()
                                    if re.findall(r'(^\d+)', debtor_and_acct, re.I):
                                        item.claim = re.findall(r'(^\d+)', debtor_and_acct, re.I)[0].strip()
                    continue

                debtor_and_acct: str = self.get_column_data(row, header_row, 'debtor')
                if not debtor_and_acct:
                    debtor_and_acct = self.get_column_data(row, header_row, 'collateral description')
                    if debtor_and_acct and debtor_and_acct.count(' ') >= 2:
                        item.claim = debtor_and_acct.split()[0]
                        item.last4digits = debtor_and_acct.split()[1]
                        item.full_name = debtor_and_acct.split(':')[-1]
                    if not item.full_name:
                        debtor_and_acct = self.get_column_data(row, header_row, 'Claim Account #')
                        if 'Debtor(s):' in debtor_and_acct:
                            item.full_name = debtor_and_acct.split('Debtor(s):')[-1].strip()
                        if re.findall(r'MONEYMART (\d{4})', debtor_and_acct, re.I):
                            item.last4digits = re.findall(r'MONEYMART (\d{4})', debtor_and_acct, re.I)[0]
                    if not item.full_name:
                        debtor_and_acct = self.get_column_data(row, header_row, 'Clm # Acct #')
                        if 'Debtor' in debtor_and_acct:
                            item.full_name = re.findall(r'Debtor\D*:(.+)', debtor_and_acct, re.I)[0].strip()
                            item.last4digits = re.findall(r'(\d{4}) Debtor\D*:', debtor_and_acct, re.I)[0].strip()
                            item.claim = re.findall(r'(^\d+)', debtor_and_acct, re.I)[0].strip()
                elif 'ACCT:' in debtor_and_acct:
                    temp_list: list = debtor_and_acct.split('ACCT:')
                    item.full_name = temp_list[0].strip()
                    item.last4digits = temp_list[-1].strip()
                else:
                    item.full_name = debtor_and_acct
                    if 'CLAIM' in item.full_name:
                        item.full_name = debtor_and_acct.split('CLAIM')[0]
                        item.claim = re.findall(r'([0-9]+)', debtor_and_acct)[0]
                if not item.last4digits:
                    item.last4digits = self.get_column_data(row, header_row, 'Account')
                    result = re.findall(r'(\d{4})', item.last4digits)
                    if result:
                        item.last4digits = result[0]
                        if len(result) > 1:
                            item.last4digits_1 = result[1]
                if not item.claim:
                    item.claim = self.get_column_data(row, header_row, 'claim')
                    if not item.claim:
                        item.claim = self.get_column_data(row, header_row, 'clm')
                        if len(item.claim.split()) == 2 and not item.last4digits:
                            item.last4digits = item.claim.split()[-1]
                            item.claim = item.claim.split()[0]
                item.amount = self.get_column_data(row, header_row, 'amount of payment')
                if not item.amount:
                    item.amount = self.get_column_data(row, header_row, 'payment')
                if not item.amount:
                    item.amount = self.get_column_data(row, header_row, 'pmt')
                if not item.amount:
                    item.amount = self.get_column_data(row, header_row, 'Balance')
                if not item.amount:
                    item.amount = self.get_column_data(row, header_row, 'total')
                    if re.findall(r'(\d+\.\d{2})', item.amount):
                        item.amount = re.findall(r'(\d+\.\d{2})', item.amount)[0]

                if not item.amount:
                    item.amount = self.get_column_data(row, header_row, 'principal')

                if not item.last4digits:
                    item.last4digits = last4digits

                if not item.full_name:
                    temp_value: str = self.get_column_data(row, header_row, 'ClaimID Acct')
                    if temp_value:
                        temp_array: list = temp_value.split()
                        if len(temp_array) > 4:
                            item.claim = temp_array[0]
                            item.last4digits = temp_array[1]
                            item.full_name = ' '.join(temp_array[3:])
                            item.case = item.case.split()[0]
                if 'case' in header_row[0].lower() and 'debtor' in header_row[0].lower() and item.case:
                    item.case = item.case.split()[0]
                    item.full_name = item.full_name.replace(item.case, '')

                second_debtor: str = self.get_column_data(row, header_row, 'Joint Debtor')
                if second_debtor:
                    item.secondary_debtor = second_debtor
                    item.secondary_debtor_last_name = second_debtor.split(',')[0]
                item.trustee_full_name = trustee_full_name
                item.trustee_state = trustee_state
                item.check_owner = check_owner
                item.check_date = check_date
                item.check_number = check_number
                if not item.claim and claim:
                    item.claim = claim

                list_of_items.append(item)
        else:
            item: InvoiceData = InvoiceData()
            item.trustee_full_name = trustee_full_name
            item.trustee_state = trustee_state
            item.check_owner = check_owner
            item.check_date = check_date
            item.check_number = check_number
            item.claim = claim

            for key, value in key_value_pair.items():
                key_lower: str = key.lower()

                if 'case' in key_lower and not item.case:
                    item.case = value
                if 'debtor' in value.lower() and not item.full_name:
                    item.full_name = re.findall(r'(.*)Debtor', value, re.I)[0].strip()
                if 'debtor' in key_lower and not item.full_name:
                    item.full_name = value
                if ('claim am' in key_lower or 'amount' in key_lower) and not item.amount:
                    item.amount = value.replace('$', '').replace(',', '')
                if 'CONTROL NO'.lower() in key_lower and not item.last4digits:
                    item.last4digits = value

            if not item.last4digits and last4digits:
                item.last4digits = last4digits
            if item.case:
                list_of_items.append(item)

        for item in list_of_items:
            item.prepare_data()

        return list_of_items
