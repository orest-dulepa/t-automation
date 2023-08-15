import os

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from libraries import common as com
from RPA.Tables import Table

from libraries.central_reach.central_reach_process.cental_reach_bulck_merge_claims import CentralReachBulkMergeClaims
from libraries.enum.payors_group import PayorsGroup
from libraries.excel import ExcelInterface
from libraries.google_drive import GoogleDrive
from libraries.models.bulk_claim_model import BulkClaimModel
from libraries.models.client_model import ClientModel
from libraries.models.payor_model import PayorModel
from libraries.models.promise_health_plan_rate_adjust_model import PromiseHealthPlanRateAdjustModel
from libraries.models.provider_item_model import ProviderItemModel
from libraries.models.timesheet_model import TimesheetModel


class ProcessBulkMergeClaims:
    def __init__(self, central_reach_obj):
        self.cr: CentralReachBulkMergeClaims = central_reach_obj
        self.gd = GoogleDrive()
        path_to_file = "mapping/Providers List.xlsx"
        self.excel = ExcelInterface(path_to_file)
        self.commercial_providers_data = self.get_commercial_providers_data()
        self.medicaid_providers_data = self.get_medicaid_providers_data()
        self.promise_health_plan_timesheets_for_processing =list()
        self.clients_data = list()
        self.client_ids_processed = set()

    def execute_bulk_merge_claims(self, payor_obj):
        com.log_message("Select and set claims by payor")
        self.cr.click_checkbox_to_select_clients()
        self.cr.action_bulk_merge_claims()
        self.cr.uncheck_all_checkboxes()
        self.cr.expand_all_and_combined_claims_view()
        if ("Optum Maryland" in payor_obj.name) or ("Presbyterian New Mexico" in payor_obj.name):
            self.cr.click_on_split_on_providers()

        if "Presbyterian New Mexico" in payor_obj.name:
            self.__change_location_and_referrer_for_all_claims__("New Mexico")


    def extract_clients_from_timesheets_data(self,timesheets):
        self.clients_data = list(dict.fromkeys(map(lambda x: x.client, timesheets)))


    def get_commercial_providers_data(self) -> list:
        table, index_row, index_of_columns = self.excel.read_sheet_and_find_headers(sheet_name="Commercial Providers (Excludes",
                                               mandatory_columns=["CLIENT",	"CLIENT_ID","PROVIDER",	"PROVIDER_ID"])
        return self.__commercial_convert_table_to_provider_items__(table,index_of_columns)

    def get_medicaid_providers_data(self) -> list:
        table, index_row, index_of_columns = self.excel.read_sheet_and_find_headers(sheet_name="Medicaid",
                                               mandatory_columns=["CLIENT",	"PROVIDER",	"PAYOR"])
        return self.__medicaid_convert_table_to_provider_items__(table,index_of_columns)

    def __commercial_convert_table_to_provider_items__(self, table: Table, index_of_column):
        providers_data = list()
        for index  in range(len(table.data)-1):
            table_row =table.data[index+1]
            provider_item: ProviderItemModel = ProviderItemModel()

            id: int = 0
            if str(table_row[index_of_column["PROVIDER_ID"]]).replace(".","").isnumeric():
                id = int(table_row[index_of_column["PROVIDER_ID"]])

            provider_item.id = id
            provider_item.name = table_row[index_of_column["PROVIDER"]]

            client_id = 0
            if str(table_row[index_of_column["CLIENT_ID"]]).replace(".","").isnumeric():
                client_id = int(table_row[index_of_column["CLIENT_ID"]])

            provider_item.client_id = client_id
            provider_item.client_name = table_row[index_of_column["CLIENT"]]
            providers_data.append(provider_item)

        return providers_data

    def __medicaid_convert_table_to_provider_items__(self, table: Table, index_of_column):
        providers_data = list()
        for index in range(len(table.data) - 1):
            table_row = table.data[index + 1]
            provider_item: ProviderItemModel = ProviderItemModel()
            provider_item.name = table_row[index_of_column["PROVIDER"]]
            provider_item.client_name = table_row[index_of_column["CLIENT"]]
            provider_item.payor_name = table_row[index_of_column["PAYOR"]]
            providers_data.append(provider_item)

        return providers_data

    def work_with_bulk_payor_claims(self,payor_obj, payors_group):
        com.log_message("Perform Checks on the Claims")
        is_last_page = False

        clients_claims_cnt = 0
        while not is_last_page:
            clients_item_ids = self.cr.get_bulk_claims_clients_of_current_page()
            com.log_message(f'{len(clients_item_ids)} clients detected per page')
            for index, client_id in enumerate(clients_item_ids):
                try:
                    if not(client_id in self.client_ids_processed):
                        self.process_bulk_claim_by_client_id(client_id, payor_obj,payors_group)
                        self.client_ids_processed.add(client_id)
                        clients_claims_cnt = len(self.client_ids_processed)
                except Exception as ex:
                    raise Exception(f"Error of client id: {client_id} - "+ str(ex))

                if clients_claims_cnt % 100 == 0 and clients_claims_cnt > 0:
                    com.log_message(f'{clients_claims_cnt} claims generated', 'INFO')

                if clients_claims_cnt == len(clients_item_ids):
                    com.log_message(f'{clients_claims_cnt} claims generated', 'INFO')


            if not self.cr.click_next_page_is_exist():
                is_last_page =True

    def process_bulk_claim_by_client_id(self, client_id, payor_obj, payors_group: PayorsGroup):
        client_elements = self.cr.browser.find_elements(f'//tr[th/span[contains(@data-bind, "clientName") and contains(text(), "{client_id}")]]')
        for index, elem_item in enumerate(client_elements):
            status_ready_xpath = f'//tr[th/span[contains(@data-bind, "clientName") and contains(text(), "{client_id}")] and td[@class="bg-success" and text()="Ready"] ]'
            items_count = self.cr.get_claims_count(xpath=status_ready_xpath)
            self.cr.find_and_navigete_to_client_elem(elem_item)
            self.cr.check_and_set_diag_code(status_ready_xpath)

            if "MBHP" in payor_obj.name:
                self.cr.set_provider_by_providers_list_in_search_field("85777", status_ready_xpath)
                self.cr.set_value_of_header_in_search_field("Location","368803", status_ready_xpath)
                self.cr.set_value_of_header_in_search_field("Referrer", "368803", status_ready_xpath)
            else:
                if PayorsGroup.COMMERCIAL == payors_group:
                    self.__providers_commercial_process_using_list_providers__(client_id, status_ready_xpath)
                elif PayorsGroup.MEDICAID == payors_group:
                    self.__providers_medicaid_process_using_list_providers__(client_id, payor_obj.name_2,status_ready_xpath)
            self.cr.execute_to_provider_supplier( xpath=status_ready_xpath)

            self.__process_of_claim_items(payor_obj=payor_obj,status_ready_xpath=status_ready_xpath, items_count=items_count)
            self.link_to_claims_inbox = self.cr.generate_this_claim_and_get_link_to_claims_inbox(xpath=status_ready_xpath, index=index)

    def __process_of_claim_items(self, payor_obj, status_ready_xpath, items_count):
        for item_index in range(items_count):
            self.cr.check_and_set_pointer_by_item(xpath=status_ready_xpath, index=item_index)
            if "CalOptima" in payor_obj.name:
                self.cr.check_on_plus_sing_caloptima_by_item(xpath=status_ready_xpath, index=item_index)

            if "MBHP" in payor_obj.name:
                self.cr.click_sync_for_client_checked_by_item(
                    xpath=status_ready_xpath + f'/following-sibling::tr/td/a[@data-syncfield="location"]/i[@class="fa fa-sync"]',
                    index=item_index)
                self.cr.click_sync_for_client_checked_by_item(
                    xpath=status_ready_xpath + f'/following-sibling::tr/td/a[@data-syncfield="referrer"]/i[@class="fa fa-sync"]',
                    index=item_index)

            self.cr.click_sync_for_client_checked_by_item(
                xpath=status_ready_xpath + '/following-sibling::tr/td/div/a/i[@class="fa fa-sync"]', index=item_index)
            self.cr.click_sync_for_client_checked_by_item(
                xpath=status_ready_xpath + f'/following-sibling::tr/td/div/a[@data-syncfield="provider"]/i[@class="fa fa-sync"]',
                index=item_index)
            self.cr.click_sync_for_client_checked_by_item(
                xpath=status_ready_xpath + f'/following-sibling::tr/td/a[@data-syncfield="providerSupplier"]/i[@class="fa fa-sync"]',
                index=item_index)

    def __providers_commercial_process_using_list_providers__(self, client_id, xpath):
        result_items = list(filter(lambda x: int(x.client_id) == int(client_id), self.commercial_providers_data))
        if len(result_items)> 0:
            current_provider_item: ProviderItemModel = result_items[0]
            self.cr.set_provider_by_providers_list_in_search_field(current_provider_item.id,xpath)

    def __providers_medicaid_process_using_list_providers__(self,client_id, payor_name, xpath):
        clients_result = list(filter(lambda x: int(x.id) == int(client_id), self.clients_data))
        if len(clients_result)>0:
            client: ClientModel = clients_result[0]
            result_items = list(filter(lambda x: (payor_name.strip().lower() in x.payor_name.strip().lower()) and client.last_name.strip().lower() in x.client_name.strip().lower(), self.medicaid_providers_data))
            if len(result_items) > 0:
                current_provider_item: ProviderItemModel = result_items[0]
                self.cr.set_provider_by_providers_list_in_search_field(current_provider_item.name, xpath)

    def __change_location_and_referrer_for_all_claims__(self, value):
        self.cr.set_value_of_header_in_search_field_sync_all("Location",value)
        self.cr.set_value_of_header_in_search_field_sync_all("Referrer",value)

    def claims_inbox_process(self,payor_obj: PayorModel) -> bool:
        com.log_message("Claims Inbox")
        self.cr.go_to_claims_inbox(self.link_to_claims_inbox)
        self.cr.update_page_of_claims_inbox()
        self.cr.minimize_pop_up_claim_export_progress()
        table_columns = self.cr.retry_get_indexes_of_columns()
        payor_claim_inbox_ids = self.cr.get_inbox_claim_ids_by_payor(payor_obj)
        com.log_message(f"Detected {len(payor_claim_inbox_ids)} claims by payor")
        amount_value_all_claims: float = 0.0

        list_promise_health_plan_rate_adjust = list()
        if "Promise Health Plan" in payor_obj.name:
            list_promise_health_plan_rate_adjust = self.get_data_of_promise_health_plan_rate_adjust()

        is_error_claims = False
        for index, claim_id in enumerate(payor_claim_inbox_ids):
            main_xpath = f'//tr[contains(@id, "billing-grid-row-{claim_id}")]'
            self.cr.navigate_to_element(main_xpath)

            if "Medicaid > Washington" in payor_obj.name:
                self.cr.medicaid_washington_process(claim_id)

            if "Promise Health Plan" in payor_obj.name:
                client_id_of_current_claims: str = self.cr.get_client_id_of_current_claims(main_xpath+f'/td/a[contains(@class, "client")]/following-sibling::div/a')
                if any(client_id_of_current_claims in str(x.client.id) for x in self.promise_health_plan_timesheets_for_processing):
                    self.cr.promise_health_plan_process(claim_id, self.promise_health_plan_timesheets_for_processing, list_promise_health_plan_rate_adjust)

            text_error = self.cr.check_errors_column(table_columns["errors"], claim_id)
            if len(text_error) > 0:
                com.log_message(
                    f"Errors from inbox claim (id: {claim_id}) of payor id: {payor_obj.id}. Error reason: " + text_error)
                is_error_claims = True

            #Molina WA
            if ('molina' in payor_obj.name.lower()) and ('washington' in payor_obj.name.lower()):
                self.cr.molina_process_item(claim_id)

            amount_value_all_claims += self.cr.get_amount_value_from_row(table_columns["amount"], claim_id)

        if is_error_claims:
            self.cr.close_tab_and_go_to_previous()
            return False

        if not(payor_obj.owed == float(amount_value_all_claims)):
            com.log_message(f"Total owed={payor_obj.owed}$ and total amounts={amount_value_all_claims}$ do not match")
            self.cr.close_tab_and_go_to_previous()
            return False

        self.cr.send_to_gateway()
        self.cr.close_tab_and_go_to_previous()
        return True

    def get_owed_total_sum(self,timesheets_data) -> float:
        owed_values = list(map(lambda x: float(x.amount_owed), timesheets_data))
        return float(sum(owed_values))

    def add_final_label(self):
        com.log_message("Add Final Label on Billings Tab")
        self.cr.reload_page()
        self.cr.add_labels()

    def get_data_of_promise_health_plan_rate_adjust(self):
        table, index_row, index_of_columns\
            = self.excel.read_sheet_and_find_headers(sheet_name="Promise Health Plan Rate Adjust",
                                                     mandatory_columns=["Time Worked", "Rounded Time","Adjusted Rate"])
        return self.__convert_table_to_promise_health_plan_rate_adjust_model(table, index_of_columns)


    def __convert_table_to_promise_health_plan_rate_adjust_model(self, table, index_of_columns):
        data = list()
        for index in range(len(table.data) - 1):
            table_row = table.data[index + 1]
            phpram_obj: PromiseHealthPlanRateAdjustModel = PromiseHealthPlanRateAdjustModel()
            phpram_obj.time_workedfloat = table_row[index_of_columns["Time Worked"]]
            phpram_obj.rounded_time = table_row[index_of_columns["Rounded Time"]]
            phpram_obj.adjusted_rate =table_row[index_of_columns["Adjusted Rate"]]
            data.append(phpram_obj)

        return data

    def check_location_item_iehp(self, item) -> bool:
        self.cr.browser.reload_page()
        return self.cr.check_location_iehp(item)

    def set_and_close_location_item_iehp(self, item):
        self.cr.reload_page()
        self.cr.set_location_iehp(item)
        self.cr.close_list_windows()










