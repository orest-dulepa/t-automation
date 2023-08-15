import datetime
import glob
import os
import time
from zipfile import ZipFile
from libraries.central_reach import CentralReach
from libraries.csv_process import CsvProcess
from libraries.excel_process import ExcelProcess
from libraries.google_drive import GoogleDrive
from libraries import common as com
from libraries.models.client_model import ClientModel
from libraries.models.columns_with_payors_data import ColumnsWithPayorsData
from libraries.waystar import WayStar
from libraries import config


class ProcessExecutor:
    def __init__(self):
        CREDENTIALS = config.get_credentials()
        self.config_data = config.get_data_using_secrets()
        self.cr : CentralReach= CentralReach(CREDENTIALS['central reach'])
        self.ws : WayStar = WayStar(CREDENTIALS['waystar'])
        self.csv_process = CsvProcess()
        self.path_to_invoice_template_csv = ''
        self.client_count = int(self.config_data['count_clients'])
        self.contacts_data_list = list()
        self.clients_collection = list()
        self.zipObjectForScreenshots = None
        self.path_to_file_with_clients = os.path.join(com.get_path_to_output(),"clients_for_processing.csv")

    @staticmethod
    def check_and_create_folders():
        if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp')):
            os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp'))

    def login_to_central_reach(self, is_need_screenshot = True):
        self.cr.login_to_central_reach(is_need_screenshot=is_need_screenshot)
        if not self.cr.is_site_available:
            com.take_screenshot(self.cr.browser, "Login_error")
            com.log_message('CentralReach site is not available', 'ERROR')
            exit(1)

    def set_filters(self, is_need_screenshot = True):
        try:
            com.log_message("Set filters")
            start_date: datetime = datetime.datetime.strptime(self.config_data["filter_start_date"], '%m/%d/%Y')
            end_date: datetime = self.cr.get_last_day_of_previous_month()
            self.cr.go_to_billing_page_with_settings(start_date, end_date)

            #self.cr.set_filter_by_2ndrv()
            self.cr.check_and_open_menu_panel()
            self.cr.apply_labels()
        except Exception as ex:
            if is_need_screenshot:
                com.take_screenshot(self.cr.browser, "Set_filters")

            raise Exception("Set Filters." + str(ex))



    def get_and_read_contacts_file(self):
        com.log_message("Get and read Contacts*.csv files")

        com.log_message('Export Contacts_clients file', 'INFO')
        path_to_file_clients = self.cr.generate_contacts_clients_files()
        com.log_message(f'Read Contacts_clients file', 'INFO')
        data_frame_clients = self.csv_process.read_file(path_to_file_clients)
        self.contacts_data_list.append(data_frame_clients)

        com.log_message('Export Contacts_clients_inactive file', 'INFO')
        path_to_file_clients_inactive = self.cr.generate_contacts_clients_inactive_files()
        com.log_message(f'Read Contacts_clients_inactive file', 'INFO')
        data_frame_clients_inactive = self.csv_process.read_file(path_to_file_clients_inactive)
        self.contacts_data_list.append(data_frame_clients_inactive)

    def work_with_clients(self):
        try:
            com.log_message(f"Start of work with client's timesheets", "INFO")
            df_clients = self.csv_process.read_file(os.path.abspath(self.path_to_file_with_clients))
            self.clients_collection = self.csv_process.get_clients_list(df_clients, self.client_count)
            com.log_message(f"{len(self.clients_collection)} - clients selected")

            for index, client_data in enumerate(self.clients_collection, 1):
                com.log_message(f"{index}) '{client_data.name}'", "INFO")
                self.process_client(client_data)

        except Exception as ex:
            com.take_screenshot(self.cr.browser, "Work_with_clients")
            com.log_message("Error during client's process. " + str(ex), "ERROR")
        finally:

            if not self.zipObjectForScreenshots is None:
                self.zipObjectForScreenshots.close()

            com.log_message("Successfully processed clients: "+ str(sum(1 for item in self.clients_collection if item.is_sucsess == True)))
            com.log_message("Fail processed clients: " + str(sum(1 for item in self.clients_collection if item.is_sucsess == False)))

    def process_client(self, client_data: ClientModel):
        current_client_name = client_data.name
        current_client_id = client_data.id
        is_success = False
        count = 0
        attempts = 3
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            if count > 0:
                com.log_message(f"The attempt of process client: " + str(count+1))

            try:
                self.cr.find_value_in_search_box(current_client_id,
                                                 f'//em[@class="filter" and contains(text(), "{current_client_id}")]')

                self.cr.is_element_available(
                    f'//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr[td/a[contains(text(),"{self.cr.get_surname(current_client_name)}")]]',
                    timeout=10)

                if not self.cr.browser.is_element_visible(
                        '//td/header/div[contains(@class,"alert-danger") and contains(text(), "No results matched")]'):
                    self.cr.mark_timesheets()
                    self.cr.bulk_generate_invoices()

                    is_need_closeout_invoices_and_statements = self.edit_invoices_and_statements(current_client_name, current_client_id)
                    if is_need_closeout_invoices_and_statements:
                        self.closeout_invoices_and_statements()
                else:
                    com.log_message("Client's rows were not found. Maybe client already processed or excess")

                client_data.is_sucsess = True
                is_success = True
            except Exception as ex:
                try:
                    path_to_screen = com.take_screenshot_of_client_to_save_in_temp(self.cr.browser, f"{current_client_id}_{current_client_name}")
                    if self.zipObjectForScreenshots is None:
                        self.zipObjectForScreenshots = ZipFile(f'{com.get_path_to_output()}/clients_error_screenshots.zip', 'w')

                    self.zipObjectForScreenshots.write(path_to_screen, os.path.basename(path_to_screen))
                except Exception as ex_:
                    pass
                com.log_message(str(exception))
                self.restart_browser()
                exception = ex
                count += 1

        if is_success is False:
            client_data.failure_reason = str(exception)
            com.log_message(f"Unable to process client. " + str(exception), "ERROR")

    def restart_browser(self):
        try:
            self.cr.close_browser()
            time.sleep(3)
            com.log_message("Restart Billing page with filters")
            self.login_to_central_reach(is_need_screenshot=False)
            self.set_filters(is_need_screenshot=False)
        except Exception as ex:
            com.log_message(f"Unable to restart Billing page. " + str(ex), "ERROR")


    def edit_invoices_and_statements(self, client_name, client_id):
        try:
            is_secondary_payor_exist, is_private_invoice_item_exist_and_clicked = self.cr.update_invoice_line_item()
            is_need_closeout_invoices_and_statements = False
            is_next_step_lockbox = True

            # private invoice
            if not is_private_invoice_item_exist_and_clicked:
                com.log_message("Update 'Private Invoice' ")
                self.cr.open_contacts_screen()
                self.cr.update_private_invoices(client_id)
                self.cr.close_all_tabs_except_first()
                self.cr.restart_page_after_update_private_invoice()
                self.cr.mark_timesheets()
                self.cr.bulk_generate_invoices()
                self.cr.select_private_invoice()

            # secondary payor
            if is_secondary_payor_exist:
                com.log_message("Review Secondary Payor")
                self.cr.open_and_set_second_billing_screen()
                is_need_generate_edited_patient_responsibility_invoice = False
                list_rows_id_by_date_range, client_data = self.cr.review_secondary_payor(client_name, client_id)
                if len(list_rows_id_by_date_range) > 0:
                    if "medicaid" in str(client_data.secondary_payor_info).lower():
                        self.cr.secondary_madicaid_process()
                    else:
                        is_need_generate_edited_patient_responsibility_invoice = self.cr.non_secondary_madicaid_process(list_rows_id_by_date_range)

                self.cr.close_all_tabs_except_first()
                if is_need_generate_edited_patient_responsibility_invoice:
                    is_next_step_lockbox = self.cr.generate_edited_patient_responsibility_invoice(client_name)

            if is_next_step_lockbox:
                self.cr.lockbox()
                self.cr.set_duedate()
                is_need_closeout_invoices_and_statements = True

            return is_need_closeout_invoices_and_statements
        except Exception as ex:
            raise Exception("Edit invoices and statements. " + str(ex))

    def closeout_invoices_and_statements(self):
        try:
            self.cr.generate_invoices()
            self.cr.closeout_invoices()
        except Exception as ex:
            raise Exception('Unable to closeout invoices and statements. '+ str(ex))

    def generate_and_download_csv_files(self):
        try:
            if not self.cr.is_browser_opened():
                self.login_to_central_reach()

            com.log_message('Generate and download "Billing*.csv" files ', 'INFO')
            self.cr.generate_billing_reports_files()

            self.cr.close_browser()
        except Exception as ex:
            com.take_screenshot(self.cr.browser, "Generate_and_download_csv_files")
            raise Exception('Unable to generate and download "*.csv" files. '+ str(ex))

    def generate_csv_report(self):
        output_report_name = "Statement"
        try:
            com.log_message(f'Generate "{output_report_name}*.csv" file ', 'INFO')
            csv_billings: dict = self.cr.downloaded_billing_csvs

            com.log_message(f'Read "Billing*.csv" files and merge with "{self.config_data["file_name_from_gd"]}"', 'INFO')
            billing_data = self.csv_process.merge_files(csv_billings, com.billings_mandatory_columns_for_csc)

            com.log_message(f'Create and calculate cells for special columns for "{output_report_name}*.csv" ', 'INFO')
            billing_data_formulas, client_ids_for_check_central_reach = self.csv_process.create_formula_results_df(billing_data, self.contacts_data_list)
            billing_data = self.csv_process.add_columns_to_df(billing_data, billing_data_formulas)
            self.csv_process.delete_excess_columns_of_billing(billing_data)

            com.log_message(f'Check and update cells of columns StatementId for "{output_report_name}*.csv" ', 'INFO')
            billing_data = self.csv_process.check_and_update_statement_id_columns(billing_data)

            com.log_message(f'Check and format cells of columns for "{output_report_name}*.csv" ', 'INFO')
            billing_data = self.check_column_values_of_billing_dataframe_via_central_reach(billing_data,
                                                                                                  client_ids_for_check_central_reach)

            com.log_message(f'Sort data by "DateOfService" and "ClientId" columns for "{output_report_name}*.csv" ', 'INFO')
            sorted_billing_data = self.csv_process.sort_data_frame(billing_data)

            com.log_message(f'Create file "{output_report_name}*.csv" and write data in to it', 'INFO')
            self.path_to_invoice_template_csv = self.csv_process.write_dataframe_to_file(sorted_billing_data, output_report_name)
            com.log_message(f'File "{os.path.basename(self.path_to_invoice_template_csv)}" was created in output folder', 'INFO')
        except Exception as ex:
            raise Exception(f'Unable to generate "{output_report_name}*.csv" file. '+ str(ex))

    def waystar_process(self):
        try:
            com.log_message(f'Upload file "{os.path.basename(self.path_to_invoice_template_csv)}" to WayStar', 'INFO')
            self.ws.login_to_site()
            self.ws.navigate_to_batches_page()
            batch_name = self.ws.upload_file(self.path_to_invoice_template_csv)
            status = self.ws.check_file_status(batch_name)
            if 'Queued for Processing' in status.text:
                com.log_message(f'{batch_name} was uploaded successfully', 'INFO')
            elif 'Error' in status.text:
                com.log_message(f'{batch_name} was not uploaded. Status: {status.text}', 'ERROR')
                com.log_message(status.text, 'ERROR')
            else:
                if status.text:
                    com.log_message(f'{batch_name} with status: {status.text}', 'ERROR')
                else:
                    raise Exception(f"{batch_name} with unexpacted Error")

            self.ws.close_browser()
        except Exception as ex:
            com.take_screenshot(self.cr.browser, "Waystar_process")
            raise Exception('Unable to upload "invoice template*.csv" file to WayStar. '+ str(ex))

    def get_data_from_excel_file(self):

        gd = GoogleDrive()
        gd.download_file_by_name(self.config_data["file_name_from_gd"])
        path_to_excel = gd.path_to_file

        excel_process = ExcelProcess(path_to_excel)
        table_invoice, index_row_invoice, index_of_columns_invoice = excel_process.read_sheet_and_find_headers(
            "invoice template 12.2017",
             mandatory_columns= com.billings_mandatory_columns_for_csc)
        data_frame_invoice = self.csv_process.convert_sheet_from_table_to_dataframe(table_invoice, com.billings_mandatory_columns_for_csc)
        print("Invoice data frame created")

        table_contacts, index_row_contacts, index_of_columns_contacts = excel_process.read_sheet_and_find_headers(
            "client contact data",
            mandatory_columns=com.contacts_mandatory_columns)
        data_frame_contacts = self.csv_process.convert_sheet_from_table_to_dataframe(table_contacts, com.contacts_mandatory_columns)
        print("Contacts data frame created")
        return data_frame_invoice, data_frame_contacts

    def check_column_values_of_billing_dataframe_via_central_reach(self, df, list_data_for_check):
        if len(list_data_for_check) > 0:
            try:
                self.cr.login_to_central_reach()
                for item_with_payor_data in list_data_for_check:
                    data_info: ColumnsWithPayorsData = self.cr.get_data_from_cr(item_with_payor_data)

                    if not data_info is None:
                        for cell_index in range(df.shape[0]):
                            if df['ClientId'][cell_index] == item_with_payor_data:
                               df['MailToFirstName'][cell_index] = data_info.mail_to_first_name
                               df['MailToLastName'][cell_index] = data_info.mail_to_last_name
                               df['MailToAddress1'][cell_index] = data_info.mail_to_address_first
                self.cr.close_browser()
            except Exception as ex:
                com.take_screenshot(self.cr.browser, "Check_column_values_via_central_reach")
                raise Exception("Unable to check column values of 'billing*.csv' via_central_reach. "+ str(ex))

        return df

    def create_txt_file_of_list_clients(self, clients):
        save_path = com.get_path_to_output()
        completeName = os.path.join(save_path, "clients.txt")
        content = ""
        keys_list = list(clients)
        for i in range(len(keys_list)):
            id = keys_list[i]
            name = clients[id]
            content += f'{i+1}) {id} - {name} \n'
        file1 = open(completeName, "w")
        file1.write(content)
        file1.close()

    def generate_list_of_clients(self):
        try:
            self.login_to_central_reach()
            self.set_filters()
            com.log_message("Generate list of clients by filter")
            self.cr.download_reports(start_year=2015)
            csv_proc = CsvProcess()
            df = csv_proc.merge_files(self.cr.downloaded_billing_csvs, ["ClientId", "ClientFirstName", "ClientLastName"])
            df.sort_values("ClientFirstName", inplace=True)
            df.drop_duplicates(subset="ClientId", keep="last", inplace=True)
            df.to_csv(self.path_to_file_with_clients)
            try:
                for file in self.cr.downloaded_billing_csvs.values():
                    os.remove(file)
                    time.sleep(2)
            except Exception as ex:
                pass
            self.cr.downloaded_billing_csvs = dict()
        except Exception as ex:
            raise Exception("Error-Generate list of clients by filter. "+ str(ex))
        finally:
            self.cr.close_browser()












