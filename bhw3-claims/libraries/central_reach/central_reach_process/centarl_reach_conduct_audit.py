import re
import time

from libraries.central_reach.central_reach import CentralReach
from libraries.models.edit_timesheet_kaiser_model import EditTimesheetKaiserModel
from libraries.models.timesheet_model import TimesheetModel
from libraries import common as com


class CentralReachConductAudit:

    def __init__(self, cr: CentralReach):
        self.cr_main = cr
        self.browser = self.cr_main.browser

    def extract_locations_from_timesheets(self, timesheets) -> list:
        return self.cr_main.extract_locations_from_timesheets(timesheets)


    def get_and_check_locations(self, acceptable_locations) -> list:
        locations_from_list = self.cr_main.cr_list_of_column_location.get_list()
        excess_location = list()
        for location_from_page in locations_from_list:
            if not self.cr_main.is_location_valid(acceptable_locations, location_from_page):
                excess_location.append(location_from_page)

        return excess_location

    def set_telehealth_location(self):
        self.cr_main.cr_list_of_column_location.select_item_from_list("Telehealth")

    def remove_telehealth(self):
        self.cr_main.cr_list_of_column_location.remove_item_filter("Telehealth")

    def get_timesheet_ids(self):
        timesheet_elems = self.cr_main.get_timesheets()
        return list(map(lambda x: self.browser.get_element_attribute(x, 'id').replace("billing-grid-row-",""), timesheet_elems))

    def add_modifier_using_edittimesheet(self, timesheetId: str, modifier: str):
        self.cr_main.go_to_by_link(f"{self.cr_main.base_url}/#billingmanager/timesheeteditor/?&id={timesheetId}")
        self.browser.reload_page()
        time.sleep(2)
        if self.browser.is_element_visible('//label[@for="modifiers"]/following-sibling::div/div/a[text()="Show modifiers"]'):
            com.click_and_wait(self.browser,'//label[@for="modifiers"]/following-sibling::div/div/a[text()="Show modifiers"]', '//div/div/div/div/input[contains(@placeholder,"Modifier")]')

            is_modifier_exist =False
            modifier_elems = self.browser.find_elements('//div/div/div/div/input[contains(@placeholder,"Modifier")]')
            for index, modifier_elem in enumerate(modifier_elems):
                if modifier in self.browser.get_element_attribute(modifier_elem, "value"):
                    is_modifier_exist = True

            time.sleep(1)

            if not is_modifier_exist:
                for index, modifier_elem in enumerate(modifier_elems):
                    if not self.browser.get_element_attribute(modifier_elem, "value"):
                        self.cr_main.input_value(modifier_elem,modifier)
                        break

                self.cr_main.wait_and_click_is_exist('//div/div/div/button/span[text()="SUBMIT"]')
                time.sleep(2)
        else:
            com.log_message(f"For timesheet #{timesheetId}: - modifiers text-boxes not exist")




    def get_duplicates_by_filter(self) -> [list]:
        filter_locator = '//em[contains(.,"Duplicate: Yes")]'
        is_success = False
        count = 0
        attempts = 4
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                self.cr_main.go_to_by_link(self.browser.location + "&isDuplicate=1")
                self.cr_main.wait_element_exist(filter_locator)
                ids = self.get_timesheet_ids()
                self.browser.go_back()
                self.browser.wait_until_page_does_not_contain_element(filter_locator)
                return ids
            except Exception as ex:
                time.sleep(3)
                exception = ex
                count += 1

        if is_success is False:
            raise exception


    def set_overlap_by_client(self):
        filter_locator = '//em[contains(.,"Overlapping: By client")]'
        self.cr_main.go_to_by_link(self.browser.location + "&isOverlapping=2")
        self.cr_main.wait_element_exist(filter_locator)

    def unset_overlap_by_client(self):
        filter_locator = '//em[contains(.,"Overlapping: By client")]'
        new_url = self.browser.location.replace("&isOverlapping=2", "")
        self.cr_main.go_to_by_link(new_url)
        self.browser.wait_until_page_does_not_contain_element(filter_locator)

    def get_clients_of_timesheets(self):
        return self.cr_main.cr_list_of_column_client.get_list()

    @staticmethod
    def get_timesheets_duplicates_by_time(timesheets_data):
        duplicates_timesheets_items = list()
        for item_timesheet in timesheets_data:
            if list(map(lambda x: x.time_str, timesheets_data)).count(item_timesheet.time_str) > 1:
                duplicates_timesheets_items.append(item_timesheet)
        return duplicates_timesheets_items

    def edit_timesheets_kaiser(self, timesheet_item: EditTimesheetKaiserModel):
        is_update_rates = timesheet_item.is_update_rates
        code = timesheet_item.code
        mod_1 ="HO"
        mod_2 ="GC"
        rates_value = "25"

        if "97153" in code:
            mod_1 = "HM"
            rates_value = "12.5"

        if "97155" in code and not is_update_rates:
            mod_2 = "HA"

        self.cr_main.go_to_by_link(f"{self.cr_main.base_url}/#billingmanager/timesheeteditor/?&id={timesheet_item.timesheet_id}")
        if self.cr_main.is_element_exist('//label[@for="modifiers"]/following-sibling::div/div/a[text()="Show modifiers"]'):
            self.cr_main.wait_and_click_is_exist('//label[@for="modifiers"]/following-sibling::div/div/a[text()="Show modifiers"]')

        modifier_elems = self.browser.find_elements('//div/div/div/div/input[contains(@placeholder,"Modifier")]')
        if not (mod_1 in self.browser.get_element_attribute(modifier_elems[0], "value")):
            self.cr_main.input_value(modifier_elems[0], mod_1)

        if not (mod_2 in self.browser.get_element_attribute(modifier_elems[1], "value")):
            self.cr_main.input_value(modifier_elems[1], mod_2)

        if is_update_rates:
            client_rate_elem = self.browser.find_element('//div/div/div/div/input[contains(@id,"rateClient")]')
            self.cr_main.input_value(client_rate_elem, rates_value)

            agreed_rate_elem = self.browser.find_element('//div/div/div/div/input[contains(@id,"rateClientAgreed")]')
            self.cr_main.input_value(agreed_rate_elem, rates_value)

        self.cr_main.wait_element_exist('//div/div/div/button/span[text()="SUBMIT"]')
        self.cr_main.wait_and_click('//div/div/div/button/span[text()="CANCEL"]')

    def get_billing_timesheets_by_payor_id_and_overlapbyclient(self, payor_id):
        return self.cr_main.get_billing_timesheets_by_payor_id(payor_id, {"isOverlapping": "2"})

    def get_billing_timesheets_by_payor_id_and_overlapbyprovider(self, payor_id):
        return self.cr_main.get_billing_timesheets_by_payor_id(payor_id, {"isOverlapping": "1"})

    def get_billing_timesheets_by_payor_kaiser_and_overlapbyclient(self):
        filter_page = {"codeLabelIdIncluded": f"{self.cr_main.claims_bot_filter['codeLabelIdIncluded']},11793,11643",
                       "isOverlapping": "2"}
        return self.cr_main.get_timesheets_by_filter_using_requests(filter_page)

    def signed_by_client_no(self):
        link_url = self.browser.location + "&signedClient=0"
        is_success = False
        count = 0
        attempts = 4
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                self.cr_main.go_to_by_link(link_url)
                self.cr_main.wait_and_click_is_exist('//em[@class="filter" and text()="Signed Client: No"]')
                timesheets_elems = self.cr_main.get_timesheets()
                if len(timesheets_elems) > 0:
                    self.cr_main.click_checkbox_to_select_clients()
                    self.cr_main.add_labels(["Invalid Signature", "Missing Signature", "Signature Audit Completed"])
                self.browser.go_back()
                is_success = True
            except Exception as ex:
                time.sleep(3)
                exception = ex
                count += 1

        if is_success is False:
            raise exception


    def signed_by_client_yes(self):
        link_url = self.browser.location + "&signedClient=1"
        is_success = False
        count = 0
        attempts = 4
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                self.cr_main.go_to_by_link(link_url)
                self.cr_main.wait_and_click_is_exist('//em[@class="filter" and text()="Signed Client: Yes"]')
                timesheets_elems = self.cr_main.get_timesheets()
                if len(timesheets_elems) > 0:
                    self.cr_main.click_checkbox_to_select_clients()
                    self.cr_main.add_labels(["Valid Signature", "Signature Audit Completed"])
                self.browser.go_back()
                is_success = True
            except Exception as ex:
                time.sleep(3)
                exception = ex
                count += 1

        if is_success is False:
            raise exception




    def close_locations_window(self):
        self.cr_main.cr_list_of_column_location.close_window_with_list()

    def add_labels_covid_19_quartine(self):
        self.cr_main.click_checkbox_to_select_clients()
        self.cr_main.add_labels(["Covid 19 Quarantine - Tele-Health Service"])

    def set_filter_covid_19(self):
        self.cr_main.find_value_in_search_box("Covid 19 Quarantine - Tele-Health Service",
              '//em[@class="filter" and contains(text(),"Covid 19 Quarantine - Tele-Health Service")]')

        if not "&pageSize" in self.browser.location:
            self.go_to_back_by_link(self.browser.location + "&pageSize=3000")


    def get_billing_timesheets_by_covid19(self, payor_id):
        filter = {"billingLabelIdIncluded" : "27694"}
        return self.cr_main.get_billing_timesheets_by_payor_id(payor_id, filter)

    def get_timesheet_for_promise_health_plan(self, payor_id):
        timesheets_list = list()
        timesheets = self.get_billing_timesheets_by_covid19(payor_id)
        for timesheet_item in timesheets:
            if ("H0031" in timesheet_item.service_auth) or ("H0032" in timesheet_item.service_auth) or (
                    "H0046" in timesheet_item.service_auth):
                timesheets_list.append(timesheet_item)

        return timesheets_list

    def process_adjustments_by_service_code(self, service_code_number: str, timesheets):
        selected_timesheets = list(filter(lambda x: (service_code_number in x.service_auth) and (float(x.time_worked_in_mins)/60 != float(x.units_of_service)), timesheets))
        if len(selected_timesheets) > 0:
            service_code_ids = list(dict.fromkeys(map(lambda x: x.procedure_code_id, selected_timesheets)))
            for service_code_id in service_code_ids:
                self.set_filter_by_service_code_id(service_code_id,service_code_number)

                selected_timesheets_by_service_code = list(dict.fromkeys(filter(lambda x: str(x.procedure_code_id) in str(service_code_id), selected_timesheets)))
                elements_after_filter = self.browser.find_elements(
                    '//*[@id="content"]/table/tbody/tr[contains(@id,"billing-grid-row") and not (contains(@class, "selected"))]')

                if len(selected_timesheets_by_service_code) == len(elements_after_filter):
                    self.cr_main.click_checkbox_to_select_clients()
                else:
                    self.cr_main.select_assign_timesheets_by_checkboxes(timesheets= selected_timesheets_by_service_code)

                self.cr_main.add_labels(["Care 1st Adjustment"])

        return selected_timesheets

    def select_timesheets(self, timesheets):
        for item in timesheets:
            timesheet_item: TimesheetModel = item
            row_id = timesheet_item.id
            xpath = f'//tr[@id="billing-grid-row-{row_id}"]/td/input[@class="select-entry"]'
            if not self.browser.is_element_visible(xpath):
                self.browser.scroll_element_into_view(xpath)

            self.cr_main.wait_and_click_is_exist(xpath)
            self.cr_main.wait_element_exist(f'//tr[@id="billing-grid-row-{row_id}" and contains(@class, "selected"]')

    def set_filter_by_service_code_id(self, service_code_id:str, service_code_number:str):
        if "&serviceCodeId=" in self.get_link_url():
            link = re.sub(r"&serviceCodeId=\d*",f"&serviceCodeId={service_code_id}", self.get_link_url())
        else:
            link = self.get_link_url() +f"&serviceCodeId={service_code_id}"

        self.cr_main.go_to_by_link(link)
        self.browser.reload_page()
        self.cr_main.wait_element_exist(xpath=f'//em[@class="filter" and contains(text(),"Service Code: {service_code_number}")]', timeout=450)

    def get_link_url(self):
        return self.cr_main.get_current_location()

    def go_to_back_by_link(self, link):
        self.cr_main.go_to_by_link(link)

