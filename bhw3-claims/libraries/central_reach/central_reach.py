import re
import time
from datetime import datetime

from libraries.central_reach.central_reach_core import CentralReachCore
from libraries.central_reach.central_reach_utils.central_reach_billing_list_of_column import CentralReachBillingListOfColumn
from libraries.models.edit_timesheet_kaiser_model import EditTimesheetKaiserModel
from libraries.models.payor_model import PayorModel


class CentralReach(CentralReachCore):

    def __init__(self, credentials: dict, input_data):
        super().__init__(credentials, input_data)
        self.cr_list_of_column_payor = CentralReachBillingListOfColumn(self.browser, "Payor")
        self.cr_list_of_column_location = CentralReachBillingListOfColumn(self.browser, "Location")
        self.cr_list_of_column_client = CentralReachBillingListOfColumn(self.browser, "Client")

        self.telehealth_formatted=''
        self.locations =list()
        self.payors_data = self.get_all_payors_data()

    def dev_attach_browser(self):
        self.browser.attach_chrome_browser(1234)
        print("browser was attached")

    def  get_link_of_billing_by_date_range_and_filters(self):
        return f"{self.base_url}/#billingmanager/billing/?startdate={self.start_date.strftime('%Y-%m-%d')}&enddate={self.end_date.strftime('%Y-%m-%d')}&billingLabelIdExcluded={self.claims_bot_filter['billingLabelIdExcluded']}&codeLabelIdIncluded={self.claims_bot_filter['codeLabelIdIncluded']}&entryStatus={self.claims_bot_filter['entryStatus']}&pageSize=3000"

    def go_to_billing_by_date_range_and_filters(self):
        link_url = self.get_link_of_billing_by_date_range_and_filters()
        self.go_to_by_link(link_url)

    def set_filters(self):
        if self.browser.does_page_contain_element('//li/a[@data-click="openMenu"]'):
            if self.browser.find_element('//li/a[@data-click="openMenu"]').is_displayed():
                self.wait_and_click_is_exist('//li/a[@data-click="openMenu"]')

        self.wait_and_click_is_exist("//li/a[text()='Filters']")

        locator_claims = "//a[@class='name label-filter']//span[contains(.,'Claims Bot')]"
        locator_saved_filters = '//div/h4/a/span[text()="Saved filters"]'
        self.wait_element_exist(locator_saved_filters)
        if not self.browser.find_element(locator_claims).is_displayed():
            self.wait_and_click_is_exist(locator_saved_filters)

        self.wait_and_click_is_exist(locator_claims)
        self.wait_element_exist('//div[@class="filters search-filters"]/div[span/em[contains(text(),"Active only")]]/'
                'following-sibling::span[div/span/em[contains(text(), "Billed")]]/'
                'following-sibling::span[div/span/em[contains(text(), "Billable")]]', timeout=120)

    def check_is_labels_set_and_set_filters(self):
        if not self.is_element_exist(
                '//div[@class="filters search-filters"]/div[span/em[contains(text(),"Active only")]]/'
                'following-sibling::span[div/span/em[contains(text(), "Billed")]]/'
                'following-sibling::span[div/span/em[contains(text(), "Billable")]]'):
            self.set_filters()

    def get_assign_payors(self, payors_dict: dict):
        all_payors = self.cr_list_of_column_payor.get_list()
        assign_payors = dict()
        payors_keys: list = list(payors_dict.keys())
        for payor_item in all_payors:
            formated_item: str = payor_item.replace(" ","").lower()
            if formated_item in payors_keys:
                assign_payors[formated_item] = payors_dict[formated_item]

        return assign_payors

    def find_payor_by_name(self, payor_item):
        payor_name = payor_item["name"]
        payor_modifier = payor_item["modifier"]
        payor_name_2 = payor_item["name_2"]
        data = list(filter(lambda x: payor_name.lower().strip() == x.name.lower().strip(), self.payors_data))
        if len(data) > 0:
            payor_obj = data[0]
            payor_obj.modifier = payor_modifier
            payor_obj.name_2 = payor_name_2
            return payor_obj
        else:
            return None

    def set_filter_of_kaiser(self)-> bool:
        new_url = self.browser.location
        if "&insuranceId=" in new_url:
            new_url = re.sub(pattern="&insuranceId=\d*", repl="", string=new_url)
        code_label_id_included_match = re.search(pattern="&codeLabelIdIncluded=\d*", string=new_url)
        code_label_id_included_str = code_label_id_included_match[0]
        new_url = new_url.replace(code_label_id_included_str, code_label_id_included_str + "-11793-11643")
        self.go_to_by_link(new_url)
        self.wait_element_exist('//div[span/em[contains(.,"Kaiser OR")]]', 120)
        self.wait_element_exist('//div[span/em[contains(.,"Kaiser Billing")]]')
        if len(self.get_timesheets()) > 0:
            return True
        else:
            return False

    def set_tricare_filter(self):
        link_url = f"{self.base_url}/#billingmanager/billing/?startdate={self.start_date.strftime('%Y-%m-%d')}&enddate={self.end_date.strftime('%Y-%m-%d')}&billingLabelIdExcluded={self.filter_tricare_audit['billingLabelIdExcluded'].replace(',','-')}&codeLabelIdIncluded={self.filter_tricare_audit['codeLabelIdIncluded'].replace(',','-')}&entryStatus={self.filter_tricare_audit['entryStatus'].replace(',','-')}"
        self.go_to_by_link(link_url)
        self.wait_element_exist('//em[@class="filter" and contains(text(),"Tricare Billing")]',120)

    def get_billing_of_tricare(self):
        filter_page: dict = self.filter_tricare_audit
        items = self.requests_obj.get_billings(start_date=self.start_date, end_date=self.end_date,
                                               page_filter=filter_page)
        timesheets_data = list(map(lambda x: self.__convert_request_items_to_timesheet_model__(x), items))
        return timesheets_data

    def get_billing_timesheets_by_payor_kaiser(self):
        filter_page = {"codeLabelIdIncluded": f"{self.claims_bot_filter['codeLabelIdIncluded']},11793,11643"}
        return self.get_timesheets_by_filter_using_requests(filter_page)

    def set_filter_by_payor_id(self, payor: PayorModel):
        link_url = self.get_link_of_billing_by_date_range_and_filters() +f"&insuranceId={payor.id}"
        self.go_to_by_link(link_url)
        self.wait_element_exist(f'//em[@class="filter" and text()="Insurance: {payor.name.replace(">","-")}"]',360)

    def is_checkbox_unselected(self, locator):
        if self.browser.is_element_visible(locator):
            if self.browser.is_checkbox_selected(locator):
                self.browser.unselect_checkbox(locator)
            self.browser.checkbox_should_not_be_selected(locator)

    def is_checkbox_selected(self, locator):
        if not self.browser.is_checkbox_selected(locator):
            self.browser.select_checkbox(locator)
        self.browser.checkbox_should_be_selected(locator)

    def get_bulk_claims_of_tricare(self):
        return self.get_bulk_claims_by_filter(self.filter_tricare_audit)

    def get_bulk_claims_of_kaiser(self):
        filter = {"codeLabelIdIncluded": f"{self.claims_bot_filter['codeLabelIdIncluded']},11793,11643"}
        filter.update(self.claims_bot_filter)
        return self.get_bulk_claims_by_filter(filter)

    def get_bulk_claims_by_payer_id(self, payor_id):
        filter: dict = {"insuranceId": payor_id}
        filter.update(self.claims_bot_filter)
        return self.get_bulk_claims_by_filter(filter)

    def get_current_location(self):
        return self.browser.location

    def set_location(self, location_name):
        self.cr_list_of_column_location.select_item_from_list(location_name)

    def close_list_window(self):
        self.cr_list_of_column_location.close_window_with_list()

    def set_filter_claims_by_payor(self, payor_obj: PayorModel):
        link_url = self.get_current_location() + f"&insuranceId={payor_obj.id}"
        self.go_to_by_link(link_url)
        self.wait_element_exist(f'//em[@class="filter" and contains(text(),"Insurance:") and contains(text(),"{payor_obj.name.replace(">", "-")}")]', 720)

    def extract_locations_from_timesheets(self, timesheets_data) -> list:
        return list(dict.fromkeys(map(lambda x: x.location, timesheets_data)))


    def close_browser(self):
        self.browser.close_all_browsers()

    def check_session_and_login_by_request(self):
        is_success = False
        count = 0
        attempts = 3
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                self.requests_obj.get_billings(start_date=datetime.today(), end_date=datetime.today())
                is_success = True
            except Exception as ex:
                print("Re-login to Central Reach")
                self.requests_obj.login_by_request()
                exception = Exception("Unable to re-login by request. " + str(ex))
                count += 1

        if is_success is False:
            raise exception

    def select_assign_timesheets_by_checkboxes(self, timesheets):
        for index, timesheet_item in enumerate(timesheets):
            self.select_checkbox_of_timesheet_by_id(timesheet_item.id)



















