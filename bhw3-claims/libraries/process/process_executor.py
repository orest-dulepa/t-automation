import os
import time
from zipfile import ZipFile

from libraries import config
from libraries.central_reach.central_reach import CentralReach
from libraries import common as com
from libraries.central_reach.central_reach_process.cental_reach_bulck_merge_claims import CentralReachBulkMergeClaims
from libraries.central_reach.central_reach_process.centarl_reach_conduct_audit import CentralReachConductAudit
from libraries.excel import ExcelInterface
from libraries.models.payor_model import PayorModel
from libraries.process.process_bulk_merge_claims import ProcessBulkMergeClaims
from libraries.process.process_conduct_audit import ProcessConductAudit
from libraries.enum.payors_group import PayorsGroup



class ProcessExecutor:

    def __init__(self):
        credentials = config.get_credentials()
        credentials['central reach']['login'] = "CClaims1"
        credentials['central reach']['password'] = credentials['central reach']['CClaims1']

        self.input_data = config.get_input()
        com.check_and_create_temp_folder()
        com.check_and_create_output_folder()
        self.cr: CentralReach = CentralReach(credentials['central reach'], self.input_data)
        self.conduct_audit_process = ProcessConductAudit(CentralReachConductAudit(self.cr))
        self.bulk_merge_claims_process = ProcessBulkMergeClaims(CentralReachBulkMergeClaims(self.cr))
        self.zipObjectForScreenshots = None
        self.is_conduct_audit_processed = False
        self.is_bulk_merge_claims_processed = False
        self.is_add_modifier_processed = False
        self.commercial_payors =list()
        self.medicaid_payors = list()
        self.read_payors_data_xlsx_to_dictionary()

    def login_and_set_filters(self):
        com.log_message("Login")
        self.cr.login_to_site()
        com.log_message(f"Open 'Billing' page by date range '{self.input_data[0]}' - '{self.input_data[1]}' "
                        f"and set filters 'Claims bot'")
        self.cr.go_to_billing_by_date_range_and_filters()

    def payors_group_process(self, payors_group: PayorsGroup):
        group_name = 'Commercial'
        list_payors: list = self.commercial_payors

        if payors_group == PayorsGroup.MEDICAID:
            group_name = "Medicaid"
            list_payors = self.medicaid_payors

        com.log_message(f"--- Start of '{group_name}' payors process ---")

        #OFF_MOCK
        # print("MOCK -TEST ONLY SELECTED PAYORS")
        # list_payors = list(filter(lambda x:
        #             ("LA Care Health Plan" in x['name']) or
        #             ("Aetna > Standard" in x['name']) or
        #             ("Blue Shield of California > Promise Health Plan" in x['name']),
        #                           list_payors))

        for index, item in enumerate(list_payors, 1):
            payor_item = item
            com.log_message(f"{index}) {payor_item['name']}")

            is_success = False
            count = 0
            attempts = 3

            self.is_conduct_audit_processed = False
            self.is_bulk_merge_claims_processed = False
            self.is_add_modifier_processed = False
            while (count < attempts) and (is_success is False):
                try:
                    if count > 0:
                        com.log_message("Attempt: "+ str(int(count+1)))
                    self.__payor_item_process__(payors_group, payor_item)
                    is_success = True
                except Exception as ex:
                    exception = Exception("Unexpected error. " + str(ex))
                    com.log_message(str(exception), 'ERROR')
                    if self.cr.is_browser_opened():
                        try:
                            path_to_screen = self.cr.take_screenshot(screen_name=f"{payor_item['name']}_error".replace(">", "").replace(" ", "_"), folder_path="temp")
                            if self.zipObjectForScreenshots is None:
                                self.zipObjectForScreenshots = ZipFile(
                                    f'{com.get_path_to_output()}/{group_name}_payors_error_screenshots.zip', 'w')

                            self.zipObjectForScreenshots.write(path_to_screen, os.path.basename(path_to_screen))
                        except Exception as ex_:
                            com.log_message("Unable to take screenshot. "+ str(ex_),'ERROR')
                    else:
                        com.log_message("Impossible take screenshot. Browser was closed", 'ERROR')

                    self.restart_browser()
                    com.log_message('Check requests session')
                    self.cr.check_session_and_login_by_request()
                    count += 1

        if not self.zipObjectForScreenshots is None:
            self.zipObjectForScreenshots.close()
            self.zipObjectForScreenshots = None

        com.log_message(f"--- End of '{group_name}' payors process ---")

    def __payor_item_process__(self, payors_group, payor_item) -> bool:
        self.cr.check_session_and_login_by_request()
        payor_obj: PayorModel = PayorModel()
        reason_msg, timesheets_data, payor_obj = self.__retry_scope_check_payor_and_get_data__(payor_item)
        if len(reason_msg) > 0:
            com.log_message(reason_msg)
            return False
        else:
            com.log_message("Payor ID: "+ str(payor_obj.id))
            com.log_message(str(len(timesheets_data)) + " timesheets available")

        if payors_group == PayorsGroup.COMMERCIAL:
            if not self.is_conduct_audit_processed:
                self.is_conduct_audit_processed = self.__commercial_conduct_audit__(payor_obj)
                if not self.is_conduct_audit_processed:
                    return False

            self.__timesheets_bulk_merge_claims__(timesheets_data, payor_obj, PayorsGroup.COMMERCIAL)

        elif payors_group == PayorsGroup.MEDICAID:
            if not self.is_conduct_audit_processed:
                self.is_conduct_audit_processed = self.__medicaid_conduct_audit__(payor_obj, timesheets_data)
                if not self.is_conduct_audit_processed:
                    return False

            if "Inland Empire Health Plan" in payor_obj.name:
                locations = config.ACCEPTABLE_LOCATIONS
                for item in locations:
                    if any(item in x.location for x in timesheets_data):
                        self.bulk_merge_claims_process.set_and_close_location_item_iehp(item)
                        self.__timesheets_bulk_merge_claims__(timesheets_data, payor_obj, PayorsGroup.MEDICAID)
            else:
                self.__timesheets_bulk_merge_claims__(timesheets_data, payor_obj, PayorsGroup.MEDICAID)

        com.log_message("Payor item was processed")

    def __commercial_conduct_audit__(self, payor_obj: PayorModel) -> bool:
        com.log_message("- Conduct Audit -")
        if "Tricare" in payor_obj.name:
            return True

        if "Kaiser" in payor_obj.name:
            timesheets_kaiser = self.cr.get_billing_timesheets_by_payor_kaiser()
            is_processed = self.conduct_audit_process.location_audit()
            if not is_processed:
                return False
            self.conduct_audit_process.kaiser_process_overlapping(timesheets_kaiser)
            self.conduct_audit_process.signature_audit()
            return True

        is_processed = self.conduct_audit_process.location_audit()
        if not is_processed:
            return False

        if not self.is_add_modifier_processed:
            self.conduct_audit_process.add_modifier_value(payor_obj.modifier)
            self.is_add_modifier_processed = True

        is_processed = self.conduct_audit_process.duplicate_entries_audit()
        if not is_processed:
            return False

        reason_msg = self.conduct_audit_process.overlapping_entries_audit_by_client(payor_id=payor_obj.id)
        if reason_msg:
            com.log_message(f"Unable to process payor: {payor_obj.name}, because were detected invalid Entry IDs: {reason_msg}")
            return False

        self.conduct_audit_process.signature_audit()
        return True

    def __medicaid_conduct_audit__(self, payor_obj: PayorModel, timesheets_data):

        if not self.is_add_modifier_processed:
            if "MHN" in payor_obj.name:
                self.conduct_audit_process.add_modifier_value(payor_obj.modifier, is_only_telehealth=False)
            else:
                self.conduct_audit_process.add_modifier_value(payor_obj.modifier)
            self.is_add_modifier_processed = True

        self.conduct_audit_process.location_audit()
        if "Optum Maryland" in payor_obj.name:
            self.conduct_audit_process.telehealth_process_for_opum(timesheets_data)

        is_processed = self.conduct_audit_process.duplicate_entries_audit()
        if not is_processed:
            return False

        self.conduct_audit_process.overlapping_entries_audit_by_provider(payor_obj.id)

        self.conduct_audit_process.signature_audit()

        if "Promise Health Plan" in payor_obj.name:
            self.bulk_merge_claims_process.promise_health_plan_timesheets_for_processing = self.conduct_audit_process.adjustments_for_promise_health_plan(payor_obj.id)

        return True

    def __retry_scope_check_payor_and_get_data__(self, payor_item: dict) -> [str, list, PayorModel]:
        is_success = False
        count = 0
        attempts = 4
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                reason_msg, timesheets_data, payor_obj = self.__check_payor_and_get_data__(payor_item)
                if (len(reason_msg) > 0) and (len(timesheets_data) >0) and (payor_obj is not None):
                    raise Exception("Unexpected error during retry scope of 'check payor and get_data'")

                return reason_msg, timesheets_data, payor_obj
            except Exception as ex:
                time.sleep(3)
                exception = Exception("Unable to check payor and get data. " + str(ex))
                count += 1

        if is_success is False:
            raise exception

    def __check_payor_and_get_data__(self, payor_item: dict) -> [str, list, PayorModel]:
        reason = ''
        payor_obj = PayorModel()
        timesheets_data = list()
        if "Tricare" in payor_item["name"]:
            self.cr.set_tricare_filter()
            timesheets_data = self.cr.get_billing_of_tricare()
            payor_obj.name = payor_item["name"]
            payor_obj.id = "6316"
        elif "Kaiser" in payor_item["name"]:
            self.cr.set_filter_of_kaiser()
            timesheets_data = self.cr.get_billing_timesheets_by_payor_kaiser()
            payor_obj.name = payor_item["name"]
            payor_obj.id = "1795"
        else:
            payor_obj = self.cr.find_payor_by_name(payor_item)
            if payor_obj is not None:
                self.cr.set_filter_by_payor_id(payor_obj)
                timesheets_data = self.cr.get_billing_timesheets_by_payor_id(payor_id=payor_obj.id)

        if len(timesheets_data) == 0:
            reason = "no one timesheets of payor item weren't found by input data range"

        return reason, timesheets_data, payor_obj

    def __timesheets_bulk_merge_claims__(self,timesheets_data: list, payor_obj: PayorModel, payors_group: PayorsGroup):
        com.log_message("- Bulk Merge Claims -")
        self.bulk_merge_claims_process.extract_clients_from_timesheets_data(timesheets_data)

        if not self.is_bulk_merge_claims_processed:
            com.log_message("Get payor total owed")
            payor_obj.owed = self.bulk_merge_claims_process.get_owed_total_sum(timesheets_data)
            com.log_message("Bulk Merge Claims Process")
            self.bulk_merge_claims_process.execute_bulk_merge_claims(payor_obj)
            self.bulk_merge_claims_process.work_with_bulk_payor_claims(payor_obj, payors_group)
            self.bulk_merge_claims_process.client_ids_processed = set()
            self.is_bulk_merge_claims_processed =True

        is_success = self.bulk_merge_claims_process.claims_inbox_process(payor_obj)
        if is_success:
            self.bulk_merge_claims_process.add_final_label()
        else:
            self.cr.browser.reload_page()

    def restart_browser(self):
        try:
            print("Restart browser")
            if self.cr.is_browser_opened():
                self.cr.close_browser()
            time.sleep(3)
            self.cr.login_to_site()
        except Exception as ex:
            raise Exception(f"Unable to restart browser. " + str(ex))

    def read_payors_data_xlsx_to_dictionary(self):
        excel = ExcelInterface("mapping/Payors_data.xlsx")
        table_commercial,index_of_columns = self.__get_sheet_table_of_payors__(excel, "commercial")
        self.commercial_payors = self.__convert_table_to_list__(table_commercial, index_of_columns)
        table_medicaid, index_of_columns = self.__get_sheet_table_of_payors__(excel, "medicaid")
        self.medicaid_payors = self.__convert_table_to_list__(table_medicaid, index_of_columns)


    def __convert_table_to_list__(self,table, index_of_columns) -> list:
        list_data: list = list()
        for index in range(len(table.data) - 1):
            table_row = table.data[index + 1]
            inner_dictionary: dict = dict()
            inner_dictionary["name"] = str(table_row[index_of_columns["name"]])
            inner_dictionary["modifier"] = str(table_row[index_of_columns["modifier"]])
            inner_dictionary["name_2"] = str(table_row[index_of_columns["name_2"]])
            list_data.append(inner_dictionary)

        return list_data

    def __get_sheet_table_of_payors__(self,excel, sheet_name):
        table, index_row, index_of_columns = excel.read_sheet_and_find_headers(sheet_name=sheet_name,
                                                                               mandatory_columns=["name", "modifier",
                                                                                                  "name_2"])
        return table, index_of_columns






