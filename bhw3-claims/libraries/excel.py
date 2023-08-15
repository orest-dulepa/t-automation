from RPA.Excel.Files import Files
from RPA.Tables import Tables
from libraries import common


class ExcelInterface:
    def __init__(self, file_path: str):
        self.file_path: str = file_path
        self.excel = Files()
        self.excel.open_workbook(file_path)

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


