import csv
import os
import math
import re
import shutil
from datetime import datetime
import pandas as pd
from pandas import DataFrame
import numpy as np
import libraries.common as com
from RPA.Tables import Table

from libraries.models.client_model import ClientModel
from libraries.models.client_statement_model import ClientStatementModel


class CsvProcess:

    @staticmethod
    def prepare_contacts_file(path_to_file: str):
        path_to_file = os.path.abspath(path_to_file)
        file_data = pd.read_csv(path_to_file)

        index = 0
        for column in file_data.keys():
            index = index + 1
            if index == 1:
                file_data.drop(column, inplace=True, axis=1)
            if index > 42:
                file_data.drop(column, inplace=True, axis=1)

        return file_data

    @staticmethod
    def prepare_billing_file(path_to_file: str):
        path_to_file = os.path.abspath(path_to_file)
        file_data = pd.read_csv(path_to_file)

        index = 0
        for column in file_data.keys():
            index = index + 1
            if index == 1:
                file_data.drop(column, inplace=True, axis=1)
            if index > 42:
                file_data.drop(column, inplace=True, axis=1)

        return file_data

    @staticmethod
    def read_file(path_to_file: str):
        try:
            path_to_file = os.path.abspath(path_to_file)
            file_data = pd.read_csv(path_to_file, low_memory=False)
            return file_data
        except Exception as ex:
            raise Exception(f"Unable to read file '{os.path.basename(path_to_file)}. "+ str(ex))

    def merge_files(self, files, mandatory_columns):
        try:
            pd.options.mode.chained_assignment = None
            new_data = self.create_dataframe_by_columns(mandatory_columns)

            for file_name in files.keys():
                file_path = files[file_name]
                try:
                    file_data = CsvProcess.read_file(file_path)
                    new_data = self.add_rows_to_dataframe(file_data, new_data, mandatory_columns)
                except Exception as ex:
                    raise Exception(f"File {os.path.basename(file_path)}. "+ str(ex))
        except Exception as ex:
            raise Exception(f"Error merge files. "+ str(ex))

        return new_data

    def get_dataframes_list(self, files):
        dataframe_list = list()
        for file_name in files.keys():
            file_path = files[file_name]
            file_data = CsvProcess.read_file(file_path)
            dataframe_list.append(file_data)

        return dataframe_list

    def add_rows_to_dataframe(self, data_frame_for_write, main_data_frame: DataFrame, mandatory_columns):
        pd.options.mode.chained_assignment = None
        rows_amount = data_frame_for_write.shape[0]
        for cell_index in range(rows_amount):
            data = dict()
            for column in mandatory_columns:
                new_cell = data_frame_for_write[column][cell_index]
                if not new_cell == column:
                    data[column] = new_cell

            new_row = data
            main_data_frame = main_data_frame.append(new_row, ignore_index=True)
        return main_data_frame

    @staticmethod
    def create_dataframe_by_columns(list_):
        dictionary_ = dict()
        for item in list_:
            if 'DateOfService' == item or \
                    'StatementDate' == item:
                dictionary_[item] = np.array([pd.Timestamp(datetime.utcnow().strftime("%m/%d/%Y"))], dtype="datetime64")

            if 'ClientId' == item or 'Id' == item or 'StatementID' == item:
                dictionary_[item] = np.array([0], dtype="int64")

            dictionary_[item] = np.array([], dtype="object")

        df = pd.DataFrame(dictionary_)
        return df

    def add_new_empty_columns_to_dataframe(self, data_frame: DataFrame, columns, count_of_last_column: int):
        index_of_col = count_of_last_column
        for column in columns:
            data_frame.insert(index_of_col, column, np.nan)
            index_of_col += 1

        return data_frame

    def add_columns_to_df(self, to_dataframe: DataFrame, from_dataframe: DataFrame):
        index_of_col = to_dataframe.shape[1]
        for column in from_dataframe.columns:
            to_dataframe.insert(index_of_col, column, from_dataframe[column])
            index_of_col += 1

        return to_dataframe

    def create_formula_results_df(self, billing_data: DataFrame, contacts_data_list):
        new_formulas_df = self.create_dataframe_by_columns(com.billings_mandatory_columns_formulas)
        client_ids_for_check_central_reach = set()
        is_need_go_to_central_reach = False
        pd.options.mode.chained_assignment = None
        for index in range(billing_data.shape[0]):
            billing_client_id = int(billing_data["ClientId"][index])

            if not billing_client_id in client_ids_for_check_central_reach:
                is_need_go_to_central_reach = False

            if self.is_client_id_exist(billing_client_id, contacts_data_list):
                column_formula = "MailToFirstName"
                contacts_column = "GuardianFirstName"
                new_value = self.get_value_from_contacts(billing_client_id, contacts_column, contacts_data_list)
                new_value = self.remove_excess_words_from_first_and_last_name(new_value)
                new_formulas_df.at[index, column_formula] = new_value
                if not is_need_go_to_central_reach:
                    is_need_go_to_central_reach = self.check_first_or_last_name(new_value)

                column_formula = "MailToLastName"
                contacts_column = "GuardianLastName"
                new_value = self.get_value_from_contacts(billing_client_id, contacts_column, contacts_data_list)
                new_value = self.remove_excess_words_from_first_and_last_name(new_value)
                new_formulas_df.at[index, column_formula] = new_value
                if not is_need_go_to_central_reach:
                    is_need_go_to_central_reach = self.check_first_or_last_name(new_value)

                column_formula = "MailToAddress1"
                contacts_column = "AddressLine1"
                new_value = self.get_value_from_contacts(billing_client_id, contacts_column, contacts_data_list)
                new_formulas_df.at[index, column_formula] = new_value
                if not is_need_go_to_central_reach:
                    is_need_go_to_central_reach = self.check_address(new_value)

                column_formula = "MailToAddress2+A:V"
                contacts_column = "AddressLine2"
                new_value = self.get_value_from_contacts(billing_client_id, contacts_column, contacts_data_list)
                new_value = self.remove_excess_words_from_address(new_value)
                new_formulas_df.at[index, column_formula] = new_value

                column_formula = "MailToCity"
                contacts_column = "City"
                new_value = self.get_value_from_contacts(billing_client_id, contacts_column, contacts_data_list)
                new_formulas_df.at[index, column_formula] = new_value

                column_formula = "MailToState"
                contacts_column = "StateProvince"
                new_value = self.get_value_from_contacts(billing_client_id, contacts_column, contacts_data_list)
                new_formulas_df.at[index, column_formula] = new_value

                column_formula = "MailToZip"
                contacts_column = "ZipPostalCode"
                new_value = self.get_value_from_contacts(billing_client_id, contacts_column, contacts_data_list)
                new_formulas_df.at[index, column_formula] = new_value
            else:
                new_value = ""
                new_formulas_df.at[index, "MailToFirstName"] = new_value
                new_formulas_df.at[index, "MailToLastName"] = new_value
                new_formulas_df.at[index, "MailToAddress1"] = new_value
                new_formulas_df.at[index, "MailToAddress2+A:V"] = new_value
                new_formulas_df.at[index, "MailToCity"] = new_value
                new_formulas_df.at[index, "MailToState"] = new_value
                new_formulas_df.at[index, "MailToZip"] = new_value

            column_formula = "CostShareDue"
            new_formulas_df.at[index, column_formula] = \
                self.get_value_from_billing(billing_data, index, "CopayOwed", "AmountAgreedOwed")

            column_formula = "StatementID"
            new_formulas_df.at[index, column_formula] = \
                self.get_value_from_billing(billing_data, index, "LastCopayInvoiceId", "LastInvoiceId")

            column_formula = "StatementDate"
            new_value = datetime.today().strftime("%m/%d/%Y")
            new_formulas_df.at[index, column_formula] = new_value

            if is_need_go_to_central_reach:
                client_ids_for_check_central_reach.add(billing_client_id)

            if index % 1000 == 0 and index > 0:
                com.log_message(f'{index} rows processed', 'INFO')

            if index == billing_data.shape[0] - 1:
                com.log_message(f'{index} rows processed', 'INFO')

        return new_formulas_df, client_ids_for_check_central_reach


    @staticmethod
    def check_first_or_last_name(name: str):
        format_name = name.strip().lower()
        if format_name == ' ':
            return True
        elif format_name == '':
            return True
        elif format_name == 'none':
            return True
        elif format_name == 'nan':
            return True
        elif format_name == '0':
            return True
        elif not format_name:
            return True

        return False

    @staticmethod
    def check_address(address: str):
        format_address = address.strip().lower()
        if "(dad" in format_address:
            return True
        elif "(mom" in format_address:
            return True
        elif format_address == '':
            return True
        elif format_address == 'none':
            return True
        elif format_address == 'nan':
            return True
        elif format_address == '0':
            return True
        elif not format_address:
            return True

        return False

    def get_value_from_contacts(self, billing_client_id, contacts_column, contacts_data_list):
        is_value_founded = False
        for i in range(len(contacts_data_list)):
            contacts_data = contacts_data_list[i]
            for cell_index in range(contacts_data.shape[0]):
                id_cell = int(contacts_data["Id"][cell_index])
                if id_cell == billing_client_id:
                    is_value_founded = True
                    finded_value = contacts_data[contacts_column][cell_index]
                    if str(finded_value).lower() in "nan" \
                            or str(finded_value).lower() in "0" \
                            or str(finded_value).lower() in "none" \
                            or finded_value is None:
                        finded_value = ''
                    return str(finded_value)

        if not is_value_founded:
            return ''

    def is_client_id_exist(self, billing_client_id, contacts_data_list):
        for i in range(len(contacts_data_list)):
            contacts_data = contacts_data_list[i]
            for cell_index in range(contacts_data.shape[0]):
                id_cell = int(contacts_data["Id"][cell_index])
                if id_cell == billing_client_id:
                    return True

        return False

    def get_value_from_billing(self, billing_data, cell_index, col_1, col_2):
        value_1 = 0
        value_2 = 0
        if not billing_data[col_1][cell_index] is None:
            if not math.isnan(billing_data[col_1][cell_index]):
                value_1 = int(billing_data[col_1][cell_index])
        if not billing_data[col_2][cell_index] is None:
            if not math.isnan(billing_data[col_2][cell_index]):
                value_2 = int(billing_data[col_2][cell_index])

        if value_1 > 0:
            new_value = value_1
        else:
            new_value = value_2

        return str(new_value)

    def write_dataframe_to_file(self, data_frame: DataFrame, file_name= "Statement"):
        path_to_template = os.path.abspath("templates/invoice template.csv")
        new_file_path = os.path.abspath(
            f"{com.get_path_to_output()}/{file_name} {datetime.utcnow().strftime('%m')} {datetime.utcnow().strftime('%Y')}.csv")
        shutil.copy(path_to_template, new_file_path)
        data_frame.to_csv(path_or_buf=new_file_path, date_format="%m/%d/%Y", index=False)
        return new_file_path

    @staticmethod
    def delete_excess_columns_of_billing(billing_data: DataFrame):
        billing_data.drop(com.billings_excess_columns_, axis='columns', inplace=True)

    def convert_sheet_from_table_to_dataframe(self, table: Table, mandatory_columns):
        df = self.create_dataframe_by_columns(mandatory_columns)
        for cell_index in range(len(table.index) - 1):
            new_row = dict()
            if cell_index > 0:
                for col_index in range(len(mandatory_columns) - 1):
                    new_cell = table.data[cell_index][col_index]
                    column = mandatory_columns[col_index]
                    new_row[column] = new_cell
                df = df.append(new_row, ignore_index=True)

        return df

    @staticmethod
    def remove_excess_words_from_first_and_last_name(name: str):
        format_str = name.strip().lower()
        reg_result = re.search(r"(\(.*?\))|(\bdad\b)|(\bmom\b)|(\bmother\b)|(\bgrand.+\b)|(\bfather\b)", format_str)
        if not reg_result is None:
            str_val = reg_result[0]
            name = format_str.replace(str_val,"")

        name = re.sub('\W+', '', name).capitalize()
        return name


    @staticmethod
    def remove_excess_words_from_address(name: str):
        if "gate code" in name.lower().strip():
            name = ''
        return name

    @staticmethod
    def convert_date_value(value_date):
        if value_date is None:
            return ''

        value_date_str = str(value_date)
        correct_match = re.search(r'^[0-3]?[0-9][/][0-3]?[0-9][/](?:[0-9]{2})?[0-9]{2}', value_date_str)
        dt = None
        if correct_match is None:
            other_form_date = re.search(r'^(?:[0-9]{2})?[0-9]{2}-[0-3]?[0-9]-[0-3]?[0-9]', value_date_str)
            if not other_form_date is None:
                dt = datetime.strptime(other_form_date[0], "%Y-%m-%d")

            other_form_date = re.search(r'^[0-3]?[0-9][.][0-3]?[0-9][.](?:[0-9]{2})?[0-9]{2}', value_date_str)
            if not other_form_date is None:
                try:
                    dt = datetime.strptime(other_form_date[0], "%m.%d.%Y")
                except:
                    dt = datetime.strptime(other_form_date[0], "%d.%m.%Y")

            other_form_date = re.search(r'^\d*[\.,]\d*$', value_date_str)
            if not other_form_date is None:
                import xlrd
                float_value = float(other_form_date[0].replace(',', '.'))
                dt = datetime(*xlrd.xldate_as_tuple(float_value, 0))

            other_form_date = re.search(r'^\d*[\.,]\d*[\.,]\d*$', value_date_str)
            if not other_form_date is None:
                import xlrd
                float_value = float(CsvProcess.remove_first_comma_or_dot(other_form_date[0]))
                dt = datetime(*xlrd.xldate_as_tuple(float_value, 0))
        else:
            dt = datetime.strptime(correct_match[0], "%m/%d/%Y")

        if not dt is None:
            return dt.strftime('%m/%d/%Y')
        else:
            return value_date

    def check_column_values_of_billing_dataframe_and_format_cells(self, df):
        for cell_index in range(df.shape[0]):
            try:
                new_value = self.convert_date_value(df['DateOfService'][cell_index])
                df['DateOfService'][cell_index] = new_value
            except Exception as ex:
                print("Unable to convert datetime - " + str(ex))

        return df

    @staticmethod
    def remove_first_comma_or_dot(value: str):
        for i in range(len(value)):
            if value[i] == ',' or value[i] == '.':
                if len(value) > i:
                    value = value[0: i:] + value[i + 1::]
                    return value.replace(',', '.')

    def get_clients_list(self, df, client_count=0):
        try:
            clients_collection = list()
            for index in range(df.shape[0]):
                if index == client_count > 0:
                    break

                if (not df["ClientId"][index] is None) or (not df["ClientFirstName"][index] is None) or (not df["ClientLastName"][index] is None):
                    id: str = str(df["ClientId"][index])
                    if not (id.lower() in "nan") or not (id.lower() in "0") or not (id.lower() in "none"):
                        client_data = ClientModel()
                        client_data.id = id
                        client_data.name = f'{df["ClientFirstName"][index]} {df["ClientLastName"][index]}'
                        clients_collection.append(client_data)

            return clients_collection
        except Exception as ex:
            raise Exception("Get clients list. " + str(ex))

    @staticmethod
    def get_clients_ids_with_different_statement_ids(data_frame: DataFrame):
        client_ids_dict = dict()
        duplicates_data_frame = data_frame[data_frame.duplicated(subset=['ClientId'], keep=False)]
        list_id_with_duplicates = np.array(duplicates_data_frame['ClientId'].array).tolist()
        list_id_with_duplicates = list(dict.fromkeys(list_id_with_duplicates))

        for item in list_id_with_duplicates:
            clients_statements = list()
            for i in range(len(duplicates_data_frame.index.values)):
                cell_index = duplicates_data_frame.index.values[i]
                if duplicates_data_frame['ClientId'][cell_index] == item:
                    m_obj = ClientStatementModel()
                    m_obj.client_id = item
                    m_obj.statement_id = duplicates_data_frame['StatementID'][cell_index]
                    m_obj.address = duplicates_data_frame['MailToAddress1'][cell_index]
                    clients_statements.append(m_obj)

            if CsvProcess.is_statement_ids_different_and_addresses_similar(clients_statements):
                client_ids_dict[item] = clients_statements[0].statement_id

        return client_ids_dict

    @staticmethod
    def is_statement_ids_different_and_addresses_similar(clients_statements):
        is_addresses_silmilar = False
        for i, item in enumerate(clients_statements):
            if i > 0 and clients_statements[i].statement_id != clients_statements[i - 1].statement_id:
                if clients_statements[i].address.replace(" ","").lower() == clients_statements[i - 1].address.replace(" ","").lower():
                    is_addresses_silmilar = True

        return is_addresses_silmilar



    @staticmethod
    def check_and_update_statement_id_columns(df):
        pd.options.mode.chained_assignment = None
        clients_with_different_st_ids = CsvProcess.get_clients_ids_with_different_statement_ids(df)
        for cell_index in range(df.shape[0]):
            client_id = df['ClientId'][cell_index]
            try:
                if client_id in clients_with_different_st_ids:
                    df['StatementID'][cell_index] = clients_with_different_st_ids[client_id]
            except Exception as ex:
                com.log_message(f"Unable to update statement_id for ClientId: {client_id}. "+str(ex))

        return df

    def sort_data_frame(self, df):
        df["DateOfService"] = pd.to_datetime(df["DateOfService"])
        sort_by_d_of_ser_and_c_id = df.sort_values(by=["DateOfService", "ClientId"])
        sort_by_d_of_ser_and_c_id["DateOfService"] = df["DateOfService"].dt.strftime('%m/%d/%Y')
        try:
            sort_by_d_of_ser_and_c_id = sort_by_d_of_ser_and_c_id.astype({"ClientId": int})
        except:
            com.log_message("Unable convert columns to 'int'")

        return sort_by_d_of_ser_and_c_id
