from RPA.Excel.Files import Files
from RPA.Tables import Tables
from libraries import common


class ExcelInterface:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.excel = Files()
        self.excel.open_workbook(file_path)

        self.payor_mapping = {}

        self.bcba_mapping = {}

        self.fee_schedule_table = None
        self.fee_schedule_header_row = 0
        self.fee_schedule_columns_index = None

        self.sca = {}
        self.sca_table = None
        self.sca_header_row = 0
        self.sca_columns_index = None

    def get_real_sheet_name(self, sheet_name: str):
        for sheet in self.excel.list_worksheets():
            if sheet.strip().lower() == sheet_name.strip().lower():
                return sheet
        common.log_message('Sheet {} not found'.format(sheet_name), 'ERROR')
        exit(1)

    def read_sheet_and_find_headers(self, sheet_name: str, mandatory_columns: list = ()):
        index_of_columns = {}
        index_row = 0
        if len(mandatory_columns) == 0:
            return index_row, index_of_columns

        table = self.excel.read_worksheet_as_table(self.get_real_sheet_name(sheet_name))
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

    def read_mapping_file(self):
        payor_table, payor_header_row, payor_columns_index = \
            self.read_sheet_and_find_headers('PayorName&FeeSchedule Ins only', ['FeeSchedule', 'PayorName'])
        for row in range(payor_header_row, len(payor_table)):
            if payor_table[row][payor_columns_index['PayorName']] is None:
                continue
            temp_name = str(payor_table[row][payor_columns_index['PayorName']]).strip().lower()
            if temp_name not in self.payor_mapping:
                self.payor_mapping[temp_name] = str(payor_table[row][payor_columns_index['FeeSchedule']])
            else:
                common.log_message('{} payor duplicated in mapping'.format(
                    str(payor_table[row][payor_columns_index['PayorName']])
                ))

        self.fee_schedule_table, self.fee_schedule_header_row, self.fee_schedule_columns_index = \
            self.read_sheet_and_find_headers('Fee Schedule detail',
                                             ['FeeSched', 'CdNum', 'CdDscrpt', 'Can Overlap', 'Cannot Overlap']
                                             )

        self.sca_table, self.sca_header_row, self.sca_columns_index = \
            self.read_sheet_and_find_headers('SCA', ['Client ID', 'Client Name', 'Payor', '2 to 1 okay'])
        for row in range(self.sca_header_row, len(self.sca_table)):
            if self.sca_table[row][self.sca_columns_index['Client ID']] is None:
                continue
            if str(self.sca_table[row][self.sca_columns_index['2 to 1 okay']]).lower() != 'yes':
                continue
            self.sca[str(self.sca_table[row][self.sca_columns_index['Client ID']]).replace('.0', '').strip().lower()] = \
                str(self.sca_table[row][self.sca_columns_index['Payor']]).lower()

        bcba_table, bcba_header_row, bcba_columns_index = \
            self.read_sheet_and_find_headers('BCBA Credential', ['Payor', 'BCBA Credentialing'])
        for row in range(bcba_header_row, len(bcba_table)):
            if bcba_table[row][bcba_columns_index['Payor']] is None:
                continue
            temp_payor = str(bcba_table[row][bcba_columns_index['Payor']]).strip().lower()
            if temp_payor not in self.bcba_mapping:
                self.bcba_mapping[temp_payor] = str(bcba_table[row][bcba_columns_index['BCBA Credentialing']])
            else:
                common.log_message('{} payor duplicated in BCBA Credentialing mapping'.format(
                    str(bcba_table[row][bcba_columns_index['Payor']])
                ))
        self.excel.close_workbook()

    def read_domo_mapping(self) -> dict:
        domo_table, domo_header_row, domo_columns_index = \
            self.read_sheet_and_find_headers('data', ['Patient ID',
                                                      'Patient Name',
                                                      'Clinician ID',
                                                      'Clinician Name',
                                                      'SchedulingSegmentHours']
                                             )

        domo_mapping = {}
        domo_table.sort_by_column(domo_table.columns[domo_columns_index['Patient ID']])
        for row in range(domo_header_row, len(domo_table)):
            try:
                client_id = str(domo_table[row][domo_columns_index['Patient ID']]).strip().replace('.0', '')
                clinician_id = str(domo_table[row][domo_columns_index['Clinician ID']]).strip().replace('.0', '')
                scheduling_segment_hours = str(domo_table[row][domo_columns_index['SchedulingSegmentHours']]).strip()
                if client_id not in domo_mapping:
                    domo_mapping[client_id] = []
                domo_mapping[client_id].append({'clinician_id': clinician_id,
                                                'hours': float('0' + scheduling_segment_hours)}
                                               )
            except Exception as ex:
                print(str(ex))

        self.excel.close_workbook()
        return domo_mapping

    def read_trump_site_list(self) -> dict:
        tsl_table, tsl_header_row, tsl_columns_index = \
            self.read_sheet_and_find_headers('Addresses', ['TBH Location Names', 'City', 'State'])
        trump_site_list = {}
        for row in range(tsl_header_row, len(tsl_table)):
            trump_site_list[str(tsl_table[row][tsl_columns_index['TBH Location Names']]).strip()] = \
                str(tsl_table[row][tsl_columns_index['City']]).strip()

        self.excel.close_workbook()
        return trump_site_list


class CsvInterface:
    def __init__(self, file_path: str):
        self.file_path = file_path
        table_obj = Tables()
        self.table = table_obj.read_table_from_csv(file_path)
        self.different_unique_places = {}

    def exported_billing_report_processing(self):
        pos_modifier = {}

        for row in self.table:
            client_id = str(row['ClientId']).strip().lower()
            procedure_code = str(row['ProcedureCode']).strip().lower()
            location_code = str(row['LocationCode']).strip().lower()
            date_of_service = str(row['DateOfService']).strip().lower()
            if client_id not in pos_modifier:
                pos_modifier[client_id] = {}
            if date_of_service not in pos_modifier[client_id]:
                pos_modifier[client_id][date_of_service] = {}
            if procedure_code not in pos_modifier[client_id][date_of_service]:
                pos_modifier[client_id][date_of_service][procedure_code] = []
            if location_code not in pos_modifier[client_id][date_of_service][procedure_code]:
                pos_modifier[client_id][date_of_service][procedure_code].append(location_code)
        for client_id, dates_of_service in pos_modifier.items():
            for date_of_service, procedure_codes in dates_of_service.items():
                for procedure_code, location_codes in procedure_codes.items():
                    if len(location_codes) > 1:
                        if client_id not in self.different_unique_places:
                            self.different_unique_places[client_id] = {}
                        if date_of_service not in self.different_unique_places[client_id]:
                            self.different_unique_places[client_id][date_of_service] = {}
                        if procedure_code not in self.different_unique_places[client_id][date_of_service]:
                            self.different_unique_places[client_id][date_of_service][procedure_code] = \
                                'Apply the modifier 76/77'
