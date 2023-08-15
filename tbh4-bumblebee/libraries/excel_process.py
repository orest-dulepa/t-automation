import os
from RPA.Excel.Files import Files

from libraries import common



class ExcelProcess:

    def __init__(self, file_path: str):
        self.file_path = os.path.abspath(file_path)
        self.excel = Files()
        self.excel.open_workbook(file_path)

    def get_real_sheet_name(self, sheet_name: str):
        for sheet in self.excel.list_worksheets():
            if sheet.strip().lower() == sheet_name.strip().lower():
                return sheet
        common.log_message('Sheet {} not found'.format(sheet_name), 'ERROR')
        exit(1)

    def read_sheet_and_find_headers(self, sheet_name: str, mandatory_columns: list = (), is_col_index_incremet_to_one: bool = False):
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
                            index_of_col: int = int(list(row.values()).index(col))
                            if is_col_index_incremet_to_one:
                                index_of_col= index_of_col+1

                            index_of_columns[mandatory] = index_of_col
            if len(index_of_columns) == len(mandatory_columns):
                break
        if len(index_of_columns) != len(mandatory_columns):
            for col in mandatory_columns:
                if col not in index_of_columns:
                    print('Column "{}" not found in mapping file'.format(col))
            exit(1)
        return table, index_row, index_of_columns

    def close_excel(self):
        self.excel.save_workbook(self.file_path)
        self.excel.close_workbook()

    def write_data_to_client_contacts_sheet(self, data, columns, last_row_index):
        self.excel.set_active_worksheet("client contact data")
        data_count = data.shape[0]
        row_index = last_row_index
        for index_of_data in range(data_count):
            self.set_cell_value_by_column("Id", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("ImgProfile", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("Credentials", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("FirstName", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("LastName", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("PermissionId", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("Email", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("LastLoginDate", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("GuardianFirstName", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("TypeId", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("IsActive", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("LastDeactivatedOn", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("LastDeactivatedBy", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("LastReactivatedOn", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("LastReactivatedBy", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("CreationDate", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("Type", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("Labels", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("AddressLine1", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("AddressLine2", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("City", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("StateProvince", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("ZipPostalCode", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("Country", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("PhoneHome", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("PhoneCell", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("PhoneWork", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("HomeAddressLine1", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("HomeAddressLine2", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("HomeCity", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("HomeStateProvince", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("HomeZipPostalCode", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("HomeCountry", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("HomePhoneHome", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("HomePhoneCell", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("HomePhoneWork", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("PrimaryLocationId", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("PrimaryLocationName", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("BirthDate", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("Gender", columns, row_index, data, index_of_data)
            self.set_cell_value_by_column("Principals", columns, row_index, data, index_of_data)
            row_index= row_index+1

        self.excel.save_workbook(self.file_path)
        self.excel.close_workbook()

    def write_data_to_billing_sheet(self,input_data_from_csv, columns, last_row_index, first_row_data_of_table):
        self.excel.set_active_worksheet("invoice template 12.2017")
        data_count = input_data_from_csv.shape[0]
        row_index = last_row_index
        for index_of_data in range(data_count):
            self.set_cell_value_by_column("Id", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("DateOfService", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("ClientId", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("ClientFirstName", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("ClientLastName", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("ProcedureCode", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("ProcedureCodeDescription", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("UnitsOfService", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("AmountAgreedOwed", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("CopayOwed", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("LastInvoiceId", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("LastInvoiceDate", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("LastCopayInvoiceId", columns, row_index, input_data_from_csv, index_of_data),
            self.set_cell_value_by_column("LastCopayInvoiceDate", columns, row_index, input_data_from_csv, index_of_data),

            self.set_cell_value_by_column_formula("MailToFirstName", columns, row_index, first_row_data_of_table),
            self.set_cell_value_by_column_formula("MailToLastName", columns, row_index, first_row_data_of_table),
            self.set_cell_value_by_column_formula("MailToAddress1", columns, row_index, first_row_data_of_table),
            self.set_cell_value_by_column_formula("MailToAddress2+A:V", columns, row_index, first_row_data_of_table),
            self.set_cell_value_by_column_formula("MailToCity", columns, row_index, first_row_data_of_table),
            self.set_cell_value_by_column_formula("MailToState", columns, row_index, first_row_data_of_table),
            self.set_cell_value_by_column_formula("MailToZip", columns, row_index, first_row_data_of_table),
            self.set_cell_value_by_column_formula("CostShareDue", columns, row_index, first_row_data_of_table),
            self.set_cell_value_by_column_formula("StatementID", columns, row_index, first_row_data_of_table),
            self.set_cell_value_by_column_formula("StatementDate", columns, row_index, first_row_data_of_table)
            row_index = row_index + 1

        self.excel.save_workbook(self.file_path)
        self.excel.close_workbook()

    def generate_data_in_invoice_temp_sheet_using_formulas(self, data, row_index, column_index):
        new_data = dict()
        return new_data

    def set_cell_value_by_column_formula(self, column_name, columns, row_index, data):
        index_of_col: int = columns[column_name] - 1
        first_cell_value_by_column = str(data[index_of_col])
        value_ = first_cell_value_by_column.replace("$C2", f"$C{row_index}")
        self.excel.set_worksheet_value(row_index, columns[column_name],value_)

    def set_cell_value_by_column(self, column_name, columns, row_index, data, index_of_data):
        if str(data[column_name][index_of_data]):
            self.excel.set_worksheet_value(row_index,
                                           columns[column_name],
                                           data[column_name][index_of_data])


