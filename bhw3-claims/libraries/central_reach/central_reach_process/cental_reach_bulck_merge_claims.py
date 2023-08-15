import re
import time

from RPA.Browser.Selenium import Selenium
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from libraries.central_reach.central_reach import CentralReach
from libraries.models.payor_model import PayorModel


class CentralReachBulkMergeClaims:
    def __init__(self, cr: CentralReach):
        self.cr_main = cr
        self.browser = self.cr_main.browser
        self.promise_health_plan_timesheets_for_processing = list()

    def click_checkbox_to_select_clients(self):
        self.cr_main.click_checkbox_to_select_clients()

    def action_bulk_merge_claims(self):
        self.cr_main.wait_and_click_is_exist('//div/a[contains(text(), "Actions")]')
        self.cr_main.wait_element_exist('//ul/li/a[contains(text(), "Bulk-merge Claims")]')

        self.cr_main.wait_and_click_is_exist('//ul/li/a[contains(text(), "Bulk-merge Claims")]')
        if self.browser.is_element_visible('//button[text()="Yes merge all billing entries"]'):
            self.cr_main.wait_and_click_is_exist('//button[text()="Yes merge all billing entries"]')
        self.cr_main.wait_element_exist('//ul/li/a[contains(text(), "Separated Claims View")]')

    def uncheck_all_checkboxes(self):
        self.cr_main.is_checkbox_unselected("//form/div/div[@class='checkbox']/label[contains(.,'Include Times')]/input")
        self.cr_main.is_checkbox_unselected("//form/div/div[@class='checkbox']/label[contains(.,'Split on Service Location')]/input")
        self.cr_main.is_checkbox_unselected("//form/div/div[@class='checkbox']/label[contains(.,'Split on Providers')]/input")
        self.cr_main.is_checkbox_unselected("//form/div/div[@class='checkbox']/label[contains(.,'Split on Authorization')]/input")

    def expand_all_and_combined_claims_view(self):
        if self.cr_main.is_element_exist('//form/div/a/span[contains(text(), "Collapse All")]'):
            self.cr_main.wait_and_click_is_exist('//form/div/a/span[contains(text(), "Collapse All")]')

        self.cr_main.wait_and_click_is_exist('//div/ul/li/a[contains(text(), "Combined Claims View")]')


    def execute_start_claims_generation_and_get_link_to_claims_inbox(self) -> str:
        if self.cr_main.is_element_exist('//button[contains(.,"Start claims generation")]'):
            self.browser.scroll_element_into_view('//button[contains(.,"Start claims generation")]')
            self.cr_main.wait_and_click_is_exist('//button[contains(.,"Start claims generation")]')

        self.cr_main.wait_element_exist('//button/following-sibling::a[contains(text(), "Go to claims inbox")]',timeout=360)
        return self.browser.find_element('//button/following-sibling::a[contains(text(), "Go to claims inbox")]').get_attribute("href")

    def generate_this_claim_and_get_link_to_claims_inbox(self, xpath: str, index)-> str:
        button_elem: WebElement = self.browser.find_elements(xpath +'/following-sibling::tr/td/button[text()="Generate this claim"]')[0]
        self.browser.scroll_element_into_view(button_elem)
        button_elem.click()

        processed_xpath = xpath.replace("Ready", "Processed")

        is_success = False
        count = 0
        attempts = 72
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                processed_element = self.browser.find_elements(processed_xpath)[index]
                is_success = True
            except Exception as ex:
                time.sleep(5)
                exception = Exception(f"Element by {processed_xpath} not available" + str(ex))
                count += 1

        if is_success is False:
            raise exception

        elems_with_link = self.browser.find_elements(processed_xpath+ "/following-sibling::tr/td/a[contains(text(),'Go to claims inbox') and not(@style='display: none;')]")
        if len(elems_with_link) > 0:
            href_str = elems_with_link[0].get_attribute("href")
        else:
            self.cr_main.wait_element_exist('//button/following-sibling::a[contains(text(), "Go to claims inbox")]',timeout=360)
            href_str = self.browser.find_element('//button/following-sibling::a[contains(text(), "Go to claims inbox")]').get_attribute("href")
        return href_str

    def go_to_claims_inbox(self, link_to_claims_inbox):
        browser_tab = self.cr_main.open_and_get_new_tab(link_to_claims_inbox)
        self.browser.switch_window(browser_tab)
        self.cr_main.wait_element_exist('//header/div/div/a[contains(text(),"Inbox")]')

    def check_and_set_diag_code(self, xpath):
        diag_code_elem = self.browser.find_element(xpath + '/descendant::td[b[text() ="Diag Codes:"]]')
        if not ('f84.0' in diag_code_elem.text.lower().split()):
            plus_elem: WebElement = \
            self.browser.find_element(xpath + '/descendant::td/a/i[@data-bind="click:showDiagcodeClick"]')
            plus_elem.click()
            textbox_xpath = xpath + '/descendant::td/span/div/a/span[@class="select2-chosen"]'
            self.cr_main.wait_and_click_is_exist(textbox_xpath)
            self.browser.scroll_element_into_view(textbox_xpath)
            id_textbox = str(self.browser.find_element(textbox_xpath).get_attribute("id")).replace("select2-chosen-",
                                                                                                   '')
            self.browser.input_text(f'//input[@id="s2id_autogen{id_textbox}_search"]', "F84.0")
            self.cr_main.wait_and_click_is_exist(
                '//div[contains(@id,"select2-result-label") and contains(text(), "F84.0")]')


    def check_and_set_pointer_by_item(self, xpath, index):
        diag_pointers_elems = self.browser.find_elements(xpath+ '/following-sibling::tr/td/input[@data-bind="value: diagPointer1"]')
        diag_pointers_elem: WebElement = diag_pointers_elems[index]
        if not("1" in diag_pointers_elem.get_attribute("value")):
            self.browser.scroll_element_into_view(diag_pointers_elem)
            self.browser.input_text(diag_pointers_elem, "1")


    def set_provider_by_providers_list_in_search_field(self, _id, xpath):
        id: str = str(_id)
        xpath_provider = xpath+'/following-sibling::tr[@class="header"]/th[contains(.,"Provider") and not(contains(.,"Supplier"))]'
        self.browser.scroll_element_into_view(xpath_provider)
        self.__set_value_of_header_in_search_field__(header_xpath=xpath_provider, header_name="Provider", text_value=id)

    def set_value_of_header_in_search_field_sync_all(self, header_name, text_value):
        header_xpath = f'//tr[th/span[contains(@data-bind, "clientName")]]/following-sibling::tr[@class="header"]/th[contains(.,"{header_name}")]'
        self.__set_value_of_header_in_search_field__(header_xpath, header_name, text_value)
        self.__execute_sync_options_to_all_claims__(header_xpath, header_name, text_value)


    def set_value_of_header_in_search_field(self, header_name, text_value, xpath):
        header_xpath = xpath + f'/following-sibling::tr[@class="header"]/th[contains(.,"{header_name}")]'
        self.__set_value_of_header_in_search_field__(header_xpath, header_name, text_value)


    def __set_value_of_header_in_search_field__(self, header_xpath, header_name, text_value):
        self.cr_main.wait_and_click_is_exist(header_xpath + "/div/a/i")
        self.cr_main.wait_and_click_is_exist(
            header_xpath + f'/div[@data-bind = "visible: show{header_name}Search"]/div/a')
        id_textbox = str(self.browser.find_element(
            header_xpath + f'/div[@data-bind = "visible: show{header_name}Search"]/div/a/span[contains(@id, "select2-chosen")]').get_attribute(
            "id")).replace("select2-chosen-", '')
        self.browser.input_text(f'//input[@id="s2id_autogen{id_textbox}_search"]', text_value)
        self.cr_main.wait_and_click_is_exist(
            f'//div[contains(@id,"select2-result-label") and contains(text(), "{text_value}")]')

    def __execute_sync_options_to_all_claims__(self, header_xpath,header_name, txt_value):
        self.cr_main.wait_and_click_is_exist(header_xpath + '/div/div/a[@data-toggle="dropdown"]')
        self.cr_main.wait_and_click_is_exist(
            header_xpath + '/div/div/ul[contains(@class,"dropdown-menu")]/li[a[contains(.,"To all claims")]]')
        self.cr_main.wait_element_exist(f'//td/a[contains(@data-bind,"{header_name.lower()}Name") and contains(text(), "{txt_value}")]')

    def execute_to_provider_supplier(self, xpath):
        value: str = self.browser.find_element(xpath+ '/following-sibling::tr/td/div/a[@data-contactid]').text
        xpath_provider = xpath + '/following-sibling::tr[@class="header"]/th[contains(.,"Provider") and not(contains(.,"Supplier"))]'
        self.browser.scroll_element_into_view(xpath_provider)
        self.cr_main.wait_and_click_is_exist(xpath_provider + '/div/div/a[@data-toggle="dropdown"]')
        self.cr_main.wait_and_click_is_exist(xpath_provider + '/div/div/ul[contains(@class,"dropdown-menu")]/li[a[contains(.,"To provider supplier")]]')
        self.cr_main.wait_element_exist(xpath + f'/following-sibling::tr[td/a[contains(@title, "{value}")]]')

    def click_sync_for_client_checked_by_item(self, xpath, index):
        sync_for_all_checked_elems = self.browser.find_elements(xpath)
        sync_for_all_checked_elem: WebElement = sync_for_all_checked_elems[index]
        self.browser.scroll_element_into_view(sync_for_all_checked_elem)
        sync_for_all_checked_elem.click()

    def send_to_gateway(self):
        self.cr_main.wait_and_click_is_exist('//th/input[@id="checkAll"]/following-sibling::label',360)
        self.cr_main.wait_and_click_is_exist('//button[contains(., "Actions")]')
        self.cr_main.wait_and_click_is_exist('//ul/li/a[text()="Send to Gateway"]')
        xpath = '//label[text() = "Choose a gateway:"]/following-sibling::div/select[@class = "form-control"]'
        self.browser.click_element_when_visible(xpath)
        self.browser.click_element_when_visible(xpath + '/option[text() = "Change Healthcare"]')
        #TODO OFF_MOCK
        #print("MOCK - click submit")

        self.cr_main.wait_and_click_is_exist('//button[text() = "Send to gateway"]')
        #self.browser.wait_and_click_button('//*[@id="modalSend"]/div[2]/div/div[1]/button')

    def check_errors_column(self, column_index, claim_id) -> str:
        text_error = self.browser.find_element(f'//tr[contains(@id, "billing-grid-row-{claim_id}")]/td[{column_index}]').text
        if len(text_error) > 0:
            return text_error

        return ''


    def get_amount_value_from_row(self, column_index, claim_id) -> float:
        return float(self.browser.find_element(f'//tr[contains(@id, "billing-grid-row-{claim_id}")]/td[{column_index}]').text.replace(',', ''))

    def molina_process_item(self, claim_id):
        browser_tab = self.cr_main.open_and_get_new_tab(self.cr_main.base_url +"/#claims/editor/?claimId="+ claim_id+ "&page=serviceLines")
        self.browser.switch_window(browser_tab)
        self.cr_main.wait_element_exist('//tbody//tr[contains(@data-bind, "$parent.editServiceLine")]')
        service_lenes_elems = self.browser.find_elements('//tbody//tr[contains(@data-bind, "$parent.editServiceLine")]')

        for index, item in enumerate(service_lenes_elems, 1):
            item.click()
            charge_value: float = \
                float(self.browser.find_element(f'//tbody//tr[contains(@data-bind, "$parent.editServiceLine")]/td[@data-bind = "currency: amount"][{index}]').text.replace("$",""))
            double_charge_value: str = str(charge_value*2)
            self.browser.input_text('//label[text() = "Charges:"]/following-sibling::div/div/input',double_charge_value, clear=True)

        self.cr_main.wait_and_click_is_exist('//button[contains(text(),"Save Claim")]')
        self.cr_main.close_tab_and_back_to_previous()
        self.browser.reload_page()

    def promise_health_plan_process(self,claim_id, need_timesheets, list_promise_health_plan_rate_adjust):
        browser_tab = self.cr_main.open_and_get_new_tab(
            self.cr_main.base_url + "/#claims/editor/?claimId=" + claim_id + "&page=serviceLines")
        self.browser.switch_window(browser_tab)

        page_timesheets = self.browser.find_elements('//tbody/tr[td/span[contains(@data-bind, "billingEntryId")]]')
        processed_page_timesheets_count: int = 0
        if len(page_timesheets) >0:
            for item in need_timesheets:
                if any(str(item.id) in x.text for x in page_timesheets):
                    self.cr_main.wait_and_click_is_exist(f'//tbody/tr[td/span[contains(@data-bind, "billingEntryId") and text()="{item.id}"]]')
                    charge_value: float = float(next(x for x in list_promise_health_plan_rate_adjust if float(x.time_workedfloat) == float(item.time_worked_in_mins)/60).adjusted_rate)
                    self.browser.input_text('//label[text() = "Charges:"]/following-sibling::div/div/input',
                                            str(charge_value), clear=True)
                    processed_page_timesheets_count +=1

            if processed_page_timesheets_count > 0:
                self.cr_main.wait_and_click_is_exist('//button[contains(text(),"Save Claim")]')

        self.cr_main.close_tab_and_back_to_previous()

    def medicaid_washington_process(self, claim_id):
        value = "103K00000X"

        browser_tab = self.cr_main.open_and_get_new_tab(self.cr_main.base_url +"/#claims/editor/?claimId="+ claim_id+ "&page=providers&tab=billing")
        self.browser.switch_window(browser_tab)
        self.__input_provider_specialtycode__("billing", value)

        self.cr_main.go_to_by_link(self.cr_main.base_url + "/#claims/editor/?claimId=" + claim_id + "&page=providers&tab=referring")
        self.__input_provider_specialtycode__("referrer", value)

        self.cr_main.wait_and_click_is_exist('//button[contains(text(),"Save Claim")]')

        self.cr_main.close_tab_and_back_to_previous()

    def __input_provider_specialtycode__(self, sub_tab_name, value):
        xpath = f'//*[@id="providers-{sub_tab_name}-specialtycode"]'
        self.cr_main.wait_element_exist(xpath)
        self.browser.scroll_element_into_view(xpath)
        self.browser.input_text(xpath, value)
        time.sleep(1)
        element_provider_billing: WebElement = self.browser.find_element(xpath)
        element_provider_billing.send_keys(Keys.ARROW_DOWN)
        time.sleep(1)
        element_provider_billing.send_keys(Keys.ENTER)
        time.sleep(1)
        if not(value in self.browser.find_element(xpath).get_attribute("value")):
            raise Exception(f"input_provider_specialtycode: invalid input value")




    def get_claims_count(self, xpath):
        return  int(self.browser.find_elements(
            xpath + '/following-sibling::tr[@class="header"]/th/span[contains(@data-bind, "claimsFlattened().length")]')[
                0].text)

    def get_bulk_claims_clients_of_current_page(self):
        elements =  self.browser.find_elements('//tbody/tr[th/span[@data-bind="text: clientName()"]]')
        clients = list(map(lambda x: re.search(r"ID:[ ]{0,}\d*",x.text)[0].lower().replace(" ", "").replace("id:",""), elements))
        return list(dict.fromkeys(clients))

    def click_next_page_is_exist(self):
        if self.browser.is_element_visible('//button[contains(@data-bind, "click:$root.bulkClaimsVm.nextClientPage")]'):
            self.browser.scroll_element_into_view('//button[contains(@data-bind, "click:$root.bulkClaimsVm.nextClientPage")]')
            self.cr_main.wait_and_click_is_exist('//button[contains(@data-bind, "click:$root.bulkClaimsVm.nextClientPage")]')
            return True

        return False

    def update_page_of_claims_inbox(self):
        link_url = self.browser.location
        if "&pageSize=" in link_url:
            link_url = re.sub(r"&pageSize=\d*","&pageSize=3000", link_url)
        else:
            link_url+= "&pageSize=3000"
        self.cr_main.go_to_by_link(link_url)
        self.cr_main.wait_element_exist('//header/div/div/a[contains(text(),"Inbox")]')

    def get_inbox_claim_ids_by_payor(self,payor_obj: PayorModel):
        self.cr_main.set_filter_claims_by_payor(payor_obj)
        xpath = f'//tr[contains(@id, "billing-grid-row-")]/td/input'
        elements = self.browser.find_elements(xpath)
        return list(map(lambda x: x.get_attribute("id"), elements))

    def get_indexes_of_columns(self):
        column_indexes = dict()
        headers_elements = self.browser.find_elements('//div[@id="content"]/table/thead/tr[@class = "header"]/th')
        for index, header in enumerate(headers_elements, 1):
            if "errors" in header.text.lower().strip():
                column_indexes["errors"] = index

            if "amount" in header.text.lower().strip():
                column_indexes["amount"] = index

            if "payor" in header.text.lower().strip():
                column_indexes["payor"] = index

        return column_indexes

    def retry_get_indexes_of_columns(self):
        is_success = False
        count = 0
        attempts = 4
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                return self.get_indexes_of_columns()
            except Exception as ex:
                time.sleep(3)
                self.browser.reload_page()
                exception = Exception("Unable to get indexes of columns. " + str(ex))
                count += 1

        if is_success is False:
            raise exception

    def close_tab_and_go_to_previous(self):
        self.cr_main.close_tab_and_back_to_previous()

    def reload_page(self):
        self.browser.reload_page()

    def add_labels(self):
        self.cr_main.click_checkbox_to_select_clients()
        self.cr_main.add_labels(["Billed"])

    def click_on_split_on_providers(self):
        self.cr_main.is_checkbox_selected("//form/div/div[@class='checkbox']/label[contains(.,'Split on Providers')]/input")

    def check_on_plus_sing_caloptima_by_item(self, xpath, index):
        elements = self.browser.find_elements(xpath + '/following-sibling::tr/td[@class="check"]')
        elem: WebElement = elements[index]
        if not ("display: none" in elem.get_attribute("style")):
            self.browser.scroll_element_into_view(elem)
            elem.click()

    def minimize_pop_up_claim_export_progress(self):
        if self.browser.is_element_visible('//div[not(contains(@class,"collapsed"))]/div/div/a/i[contains(@class, "far fa-fw fa-window-minimize")]'):
            self.cr_main.wait_and_click_is_exist('//div[not(contains(@class,"collapsed"))]/div/div/a/i[contains(@class, "far fa-fw fa-window-minimize")]')

    def navigate_to_element(self, xpath):
        self.browser.scroll_element_into_view(xpath)

    def find_and_navigete_to_client_elem(self, elem_item):
        self.browser.scroll_element_into_view(elem_item)

    def get_client_id_of_current_claims(self, xpath):
        elem: WebElement = self.browser.find_element(xpath)
        return elem.get_attribute("contactid")

    def check_location_iehp(self, location) -> bool:
        list_of_locations = self.cr_main.cr_list_of_column_location.get_list()
        return any(location in x for x in list_of_locations)

    def set_location_iehp(self, location):
        self.cr_main.cr_list_of_column_location.select_item_from_list(location)

    def close_list_windows(self):
        self.cr_main.cr_list_of_column_location.close_window_with_list()