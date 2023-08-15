from RPA.Excel.Files import Files
from RPA.Tables import Table
from libraries import common
import datetime
from libraries.eob import EOB, ACNT, Service


class ExcelInterface:
    def __init__(self, file_path: str):
        self.file_path: str = file_path
        self.excel = Files()

        self.current_valid_sheet: str = ''
        self.current_valid_dt: Table = Table()
        self.current_valid_date: datetime = None
        self.processed_sheets: list = []



        self.payor_mapping: dict = {}
        self.fee_schedule_rates = None
        self.fsr_headers: dict = {}

        self.bcba_mapping: dict = {}

        self.fee_schedule_table = None
        self.fee_schedule_header_row: dict = {}
        self.fee_schedule_columns_index: dict = {}

        self.sca = {}
        self.sca_table = None
        self.sca_header_row = 0
        self.sca_columns_index = None

        self.npi = {}

    def get_real_sheet_name(self, sheet_name: str):
        for sheet in self.excel.list_worksheets():
            if sheet.strip().lower() == sheet_name.strip().lower():
                return sheet
        common.log_message('Sheet {} not found'.format(sheet_name), 'ERROR')
        exit(1)

    def read_sheet_and_find_headers(self, sheet_name: str, mandatory_columns: list = (), header: bool = False):
        index_of_columns: dict = {}
        index_row: int = 0
        table = self.excel.read_worksheet_as_table(self.get_real_sheet_name(sheet_name), header)
        if len(mandatory_columns) == 0:
            return table, index_row, index_of_columns

        for row in table:
            index_row += 1
            for col in row.values():
                if col is not None:
                    tmp_col = str(col).strip().lower()
                    if tmp_col in index_of_columns:
                        continue
                    for mandatory in mandatory_columns:
                        if tmp_col == mandatory.lower():
                            index_of_columns[mandatory] = list(row.values()).index(col)
            if len(index_of_columns) == len(mandatory_columns):
                break
        if len(index_of_columns) != len(mandatory_columns):
            for col in mandatory_columns:
                if col not in index_of_columns:
                    print('Column "{}" not found in mapping file'.format(col))
            exit(1)
        return table, index_row, index_of_columns

    def read_current_month_cash_disbursement(self):
        self.excel.open_workbook(self.file_path)

        self.current_valid_sheet: str = ''
        self.current_valid_dt: Table = Table()
        for sheet in self.excel.list_worksheets():
            if sheet in self.processed_sheets:
                continue
            if sheet.isdigit():
                try:
                    self.current_valid_dt = self.excel.read_worksheet_as_table(sheet, True)
                    for row in self.current_valid_dt.iter_dicts():
                        if row['Check Number'] is not None and row['Applied'] is None and\
                                str(row['Payer Type']).strip().lower() != 'Patient Resp'.lower() and\
                                'ERA - NON'.lower() not in str(row['Deposit Account']).strip().lower():
                            self.current_valid_sheet = sheet
                            self.processed_sheets.append(sheet)
                            self.current_valid_date = row['Date']
                            break
                        if row['Check Number'] is None and row['Funding Source'] is None:
                            break
                    if self.current_valid_sheet:
                        break
                    self.current_valid_dt.clear()
                except Exception as ex:
                    print(f'Excel error. Sheet {sheet}')
                    print(str(ex))
        self.excel.close_workbook()
        if self.current_valid_sheet:
            print(f'Found valid sheet {self.current_valid_sheet}')
        else:
            print('All sheets processed. End run')

    def write_to_current_month_cash_disbursement(self, row_index: int, status: str, amount: float = 0.0):
        row_index += 2  # +1 because index start from 0 and +1 because header used
        self.excel.open_workbook(self.file_path)

        # Applied column
        self.excel.set_worksheet_value(row_index, 5, status, self.current_valid_sheet)
        if status.lower() == 'x':
            # Central Reach column
            self.excel.set_worksheet_value(row_index, 6, amount, self.current_valid_sheet)

        self.excel.save_workbook()
        self.excel.close_workbook()

    def read_lockbox_remit(self, check_number: str) -> (EOB, dict):
        self.excel.open_workbook(self.file_path)

        eob_data: EOB = EOB()
        self.current_valid_sheet: str = ''
        for sheet in self.excel.list_worksheets():
            if check_number.lower() in str(sheet).lower():
                self.current_valid_sheet = sheet
                eob_data.eft_number = check_number
                eob_data.lockbox = True
                break

        acnt_data: dict = {}
        if self.current_valid_sheet:
            temp_dt: Table = self.excel.read_worksheet_as_table(self.current_valid_sheet, True)
            for row in temp_dt.iter_dicts():
                if row['ACNT'] is None:
                    break
                acnt_number: str = str(row['ACNT']).replace('.0', '')
                current_acnt: ACNT = ACNT(acnt_number)
                billed_amount: float = 0.0
                try:
                    billed_amount = float(row['Billed Amount'])
                except:
                    try:
                        if 'Units' in row:
                            billed_amount = round(float(row['Units']) * float(row['Rate Per Unit']), 2)
                        elif 'Hours' in row:
                            billed_amount = round(float(row['Hours']) * float(row['Rate Per Hour']), 2)
                    except Exception as ex:
                        print(str(ex))

                cpt_code: str = row['Code']
                if len(cpt_code.split()[0].strip()) == 5:
                    cpt_code = cpt_code.split()[0].strip()

                current_acnt.services.append(
                    Service(
                        cpt_code,
                        row['PAYMENT DATE'],
                        billed_amount,
                        billed_amount,
                        billed_amount,
                        {}
                    )
                )
                if acnt_number not in acnt_data:
                    acnt_data[acnt_number] = current_acnt
                else:
                    acnt_data[acnt_number].services += current_acnt.services

        self.excel.close_workbook()
        return eob_data, acnt_data
