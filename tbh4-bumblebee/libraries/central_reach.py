import glob

from RPA.Browser.Selenium import Selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from libraries import common as com
from urllib.parse import urlparse
from zipfile import ZipFile
import datetime
import time
import os
import shutil
import re

from libraries.models.client_model import ClientModel
from libraries.models.clinent_secondary_payor_model import ClientSecondaryPayorModel
from libraries.models.columns_with_payors_data import ColumnsWithPayorsData

class CentralReach:

    downloaded_pdf_invoices = dict()
    downloaded_billing_csvs = dict()
    downloaded_contacts_csvs = dict()

    def __init__(self, credentials: dict,):
        self.browser: Selenium = Selenium()
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.base_url = self.get_base_url()
        self.link_of_billing_tab_with_date_range = ""
        self.id_label_inv_cur_month = ''
        self.id_label_error = ''
        self.employee_id: str = ''
        self.error_label_name = "Error_client"
        self.downloaded_billing_csvs = dict()

    #============================TEST====================================================
    def dev_attach_browser(self):
        self.browser.attach_chrome_browser(1234)
        if self.browser.does_page_contain_element('//*[@id="domain-members"]'):
            print("browser was attached")

    def dev_cancel(self):
        elems = self.browser.find_elements('//div/a[text() = "Cancel" and @data-bind="click: cancel, visible: !creatingInvoices()"]')
        elems[1].click()

    def dev_check_or_uncheck(self):
        self.browser.click_element_when_visible('//*[@id="content"]/table/thead/tr/th/input[@data-bind="checked: listVm.allSelected"]')

    # ============================TEST====================================================

    def get_base_url(self):
        parsed_uri = urlparse(self.url)
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

    def close_browser(self):
        self.browser.close_browser()

    def is_browser_opened(self)-> bool:
        try:
            title = self.browser.driver.title
            return True
        except Exception as ex:
            return False

    def is_element_available(self, locator, timeout=90) -> bool:
        try:
            com.wait_element(self.browser, locator, timeout=timeout)
            return True
        except Exception as ex:
            return False

    def login_to_central_reach(self, is_need_screenshot = True) -> object:
        self.browser.close_browser()
        self.browser.timeout = 45
        self.is_site_available = False
        count = 1
        path_to_temp = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'cr')
        if os.path.exists(path_to_temp):
            shutil.rmtree(path_to_temp)
        os.mkdir(path_to_temp)
        preferences = {
            'download.default_directory': os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'cr'),
            'plugins.always_open_pdf_externally': True,
            'download.directory_upgrade': True,
            'download.prompt_for_download': False
        }

        while count <= 3 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.url, preferences=preferences)
                self.browser.set_window_size(1920, 1080)
                self.browser.maximize_browser_window()
                com.wait_element(self.browser, "//input[@type='password']", timeout=10)
                if self.browser.does_page_contain_element("//p[text()='Scheduled Maintenance']"):
                    if self.browser.find_element("//p[text()='Scheduled Maintenance']").is_displayed():
                        com.log_message("Logging into CentralReach failed. Scheduled Maintenance.".format(count),
                                           'ERROR')
                        if is_need_screenshot:
                            self.browser.capture_page_screenshot(
                                os.path.join(
                                    os.environ.get("ROBOT_ROOT", os.getcwd()),
                                    'output',
                                    'Centralreach_scheduled_maintenance.png')
                            )
                        return
                com.wait_element(self.browser, "//input[@type='password']")
                self.browser.input_text_when_element_is_visible("//input[@type='text']", self.login)
                self.browser.input_text_when_element_is_visible("//input[@type='password']", self.password)
                self.browser.click_button_when_visible("//button[@class='btn']")
                if self.browser.does_page_contain_element('//div[@class="loginError"]/div[text()="There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support"]'):
                    elem = self.browser.find_element('//div[@class="loginError"]/div[text()="There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support"]')
                    if elem.is_displayed():
                        com.log_message("Logging into CentralReach failed. There was an unexpected problem signing in.".format(count), 'ERROR')
                        raise Exception("There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support")
                com.wait_element_and_refresh(self.browser, "//span[text()='Favorites']")
                self.is_site_available = self.browser.does_page_contain_element("//span[text()='Favorites']")

                if self.is_site_available:
                    self.employee_id = str(
                        self.browser.get_text("//span/span[text()='Employee']/../../span[@class='pull-right']")).strip()

            except Exception as ex:
                com.log_message("Logging into CentralReach. Attempt #{} failed".format(count), 'ERROR')
                print(str(ex))
                if is_need_screenshot:
                    self.browser.capture_page_screenshot(
                        os.path.join(
                            os.environ.get("ROBOT_ROOT", os.getcwd()),
                            'output',
                            'Centralreach_login_failed_{}.png'.format(count)
                        )
                    )
                self.browser.close_browser()
            finally:
                count += 1

    def go_to_by_link(self, link_url: str):
        self.browser.go_to(link_url)

    def go_to_billing_page_with_settings(self, start_date, end_date, per_page="1000"):
        is_success = False
        count = 0
        attempts = 4
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                self.link_of_billing_tab_with_date_range = self.base_url + '#billingmanager/billing/?startdate={}&enddate={}'.format(
                    start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                self.browser.go_to(
                    self.link_of_billing_tab_with_date_range + '&pageSize={}&sort=client&copayStatus=2&billingLabelIdExcluded=15565'.format(
                        per_page))
                com.wait_element(self.browser, "//th//div//a//span[contains(.,'Client')]", timeout=20)
                is_success = True
            except Exception as ex:
                exception = Exception("Go to billing tab. " + str(ex))
                count += 1

        if is_success is False:
            raise exception

    def open_and_set_second_billing_screen(self):
        try:
            browser_tab = self.open_and_get_new_tab(
                self.link_of_billing_tab_with_date_range + "&sort=date&pageSize=1000&copayStatus=2")

            self.browser.switch_window(browser_tab)
            if not self.is_element_available(
                    '//*[@id="content"]/table/thead/tr/td/header/div/div/div/div/span/em[text() ="Patient Responsibility Status: Outstanding" ]', timeout=60):
                print("The label 'Patient Responsibility Status: Outstanding' is not exist. Need add")
                self.click_on_pr_amt_outstanding()
            self.check_is_need_reload_page()
        except Exception as ex:
            raise Exception("Open and set 2nd billing screen. " + str(ex))

    def close_tab_and_back_to_previous(self):
        browser_tabs = self.browser.get_window_handles()
        self.browser.close()
        self.browser.switch_window(browser_tabs[0])

    def check_and_open_menu_panel(self):
        try:
            if self.browser.does_page_contain_element('//li/a[@data-click="openMenu"]'):
                if self.browser.find_element('//li/a[@data-click="openMenu"]').is_displayed():
                    com.log_message('data-click="openMenu"')
                    com.click_and_wait(self.browser, '//li/a[@data-click="openMenu"]', "//li/a[text()='Filters']")
        except Exception as ex:
            raise Exception("Check and open menu panel. " + str(ex))

    @staticmethod
    def get_last_day_of_previous_month():
        return datetime.datetime.utcnow().replace(day=1) - datetime.timedelta(days=1)

    def apply_labels(self):
        try:
            com.wait_element(self.browser, "//li/a[text()='Labels']")
            self.browser.click_element_when_visible("//li/a[text()='Labels']")
            self.check_and_open_patient_invoices()
            self.click_on_invoice_current_month()
            self.parse_id_label_cur_month_from_url()

            if not self.browser.is_element_visible("//em[contains(.,'DO NOT SEND INVOICE') and contains(.,'exclude')]"):
                self.click_on_do_not_send_invoice()

            if not self.browser.is_element_visible(
                    '//*[@id="content"]/table/thead/tr/td/header/div/div/div/div/span/em[text() ="Patient Responsibility Status: Outstanding" ]'):
                self.click_on_pr_amt_outstanding()

        except Exception as ex:
            raise Exception("Apply labels. " + str(ex))

    def parse_id_label_cur_month_from_url(self):
        str_arr_buff = self.browser.location.replace("&billingLabelIdExcluded=", '/').split('/')
        last_numbers = str_arr_buff[len(str_arr_buff) - 1].split('-')
        self.id_label_inv_cur_month = last_numbers[1]


    def find_and_click_on_fa_caret_right(self):
        items_of_organization_labels = self.browser.find_elements("//div[@id='collapseTagsPublic']/div/ol/li[@class "
                                                                  "='rail-tags-item']")
        for item_label in items_of_organization_labels:
            if item_label.text.find("Patient Invoices") != -1:
                children = item_label.find_elements(By.XPATH, "child::*")
                children[0].click()
                break

    def check_and_open_patient_invoices(self):
        try:
            locator_do_not_send_invoice = "//a[@class='name label-filter']//span[contains(.,'DO NOT SEND INVOICE')]"
            com.wait_element(self.browser, "//li[@class='rail-tags-item']//a//span[contains(.,'Patient Invoices')]")
            if not self.browser.find_element(locator_do_not_send_invoice).is_displayed():
                com.click_and_wait(self.browser,
                    "//li[@class='rail-tags-item']//a[span[contains(.,'Patient Invoices')]]/preceding-sibling::a[@data-click='expand' and not(@style = 'display: none;')]",
                                   locator_do_not_send_invoice)
        except Exception as ex:
            raise Exception("Check and open 'Patient Invoices'. " + str(ex))

    def create_and_set_error_label(self):
        try:
            locator_with_label = f"//a[@class='name label-filter']//span[contains(.,'{self.error_label_name}')]"

            if self.browser.is_element_visible("//h4[@class='panel-title']/a[@aria-expanded='false']/span[text()='Private labels']/preceding-sibling::i[@class='fa fa-caret-down pull-left']"):
                self.browser.click_element_when_visible("//h4[@class='panel-title']/a[@aria-expanded='false']/span[text()='Private labels']/preceding-sibling::i[@class='fa fa-caret-down pull-left']")

            if not self.browser.is_element_visible(locator_with_label):
                self.browser.click_element_when_visible('//h4[@class="panel-title"]/a[span[text()="Private labels"]]/preceding-sibling::a[@class="pull-right manage-tags"]/i[@class="fa fa-cog"]')
                self.browser.click_element_when_visible('//*[@id="tagsSelect"]')
                com.click_and_wait(self.browser,'//*[@id="tagsSelect"]', '//*[@id="tagsSelect"]/option[text()="Add new label"]')
                com.click_and_wait(self.browser,'//*[@id="tagsSelect"]/option[text()="Add new label"]', '//*[@id="tagsName"]')
                self.browser.input_text('//*[@id="tagsName"]', self.error_label_name)
                self.browser.click_element_when_visible('//*[@id="billingmanager-billing-sub-module"]/div/div/div/div/div/div/button[text()="Create label"]')
                self.browser.wait_until_page_does_not_contain('//*[@id="billingmanager-billing-sub-module"]/div/div/div/div/div/div/button[text()="Create label"]')
                self.browser.click_element_when_visible('//div[@class="modal-content"]/div[@class = "modal-footer label-modal-footer"]/div/button[text()="Cancel"]')
                com.wait_element(self.browser, locator_with_label)

            com.click_and_wait(self.browser, locator_with_label,
                               f"//em[contains(.,'{self.error_label_name}')]")
            com.click_and_wait(self.browser, locator_with_label,
                               f"//em[contains(.,'{self.error_label_name}') and contains(.,'exclude')]")

            str_arr_buff = self.browser.location.replace("&billingLabelIdExcluded=", '/').split('/')
            last_numbers = str_arr_buff[len(str_arr_buff) - 1].split('-')
            self.id_label_error = last_numbers[len(last_numbers)-1]

        except Exception as ex:
            raise Exception("Unable to create temporary error label. " + str(ex))

    def remove_error_label(self):
        try:
            if not self.is_browser_opened():
                self.login_to_central_reach(is_need_screenshot=False)

            self.go_to_by_link(self.base_url + '#billingmanager/billing')
            self.check_and_open_menu_panel()
            com.wait_element(self.browser, "//li/a[text()='Labels']")
            self.browser.click_element_when_visible("//li/a[text()='Labels']")

            com.wait_element(self.browser, '//h4[@class="panel-title"]/a[span[text()="Private labels"]]/preceding-sibling::a[@class="pull-right manage-tags"]/i[@class="fa fa-cog"]', timeout=60)
            com.click_and_wait(self.browser,'//h4[@class="panel-title"]/a[span[text()="Private labels"]]/preceding-sibling::a[@class="pull-right manage-tags"]/i[@class="fa fa-cog"]','//*[@id="tagsSelect"]')
            self.browser.click_element_when_visible('//*[@id="tagsSelect"]')
            com.click_and_wait(self.browser,f'//*[@id="tagsSelect"]', f'//*[@id="tagsSelect"]/option[text()="{self.error_label_name}"]')
            com.click_and_wait(self.browser,f'//*[@id="tagsSelect"]/option[text()="{self.error_label_name}"]', '//*[@id="tagsName"]')

            self.browser.click_element_when_visible(
                '//div[@class="modal-content"]/div[@class = "modal-footer label-modal-footer"]/div/span/input')
            self.browser.click_element_when_visible('//div[@class="modal-content"]/div[@class = "modal-footer label-modal-footer"]/div/button[text()="Remove"]')
            self.browser.wait_until_page_does_not_contain('//div[@class="modal-content"]/div[@class = "modal-footer label-modal-footer"]/div/button[text()="Remove"')
            self.browser.click_element_when_visible('//div[@class="modal-content"]/div[@class = "modal-footer label-modal-footer"]/div/button[text()="Cancel"]')
            #self.browser.click_element_when_visible(f'//div[@class="filters search-filters"]/span/div/span/em[contains(.,"{self.error_label_name}")]/following-sibling::a[@class="remove"]')
            self.browser.reload_page()

        except Exception as ex:
            com.log_message("Unable to remove temporary error label. " + str(ex), 'ERROR')

    def check_and_open_errors(self):
        try:
            locator = "//a[@class='name label-filter']//span[contains(.,'Errors')]"
            com.wait_element(self.browser, "//li[@class='rail-tags-item']//a//span[contains(.,'CSST')]")

            if not self.browser.find_element(locator).is_displayed():
                self.browser.click_element_when_visible("//li[@class='rail-tags-item']//a[span[contains(.,'CSST')]]/preceding-sibling::a[@data-click='expand' and not(@style = 'display: none;')]")
                com.click_and_wait(self.browser, locator,
                                   "//em[contains(.,'DO NOT SEND INVOICE')]")
                com.click_and_wait(self.browser, locator,
                                   "//em[contains(.,'DO NOT SEND INVOICE') and contains(.,'exclude')]")

        except Exception as ex:
            raise Exception("Check and open 'Errors' label . " + str(ex))

    def click_on_do_not_send_invoice(self):
        try:
            locator_do_not_send_invoice = "//a[@class='name label-filter']//span[contains(.,'DO NOT SEND INVOICE')]"
            com.click_and_wait(self.browser, locator_do_not_send_invoice,
                               "//em[contains(.,'DO NOT SEND INVOICE')]")
            com.click_and_wait(self.browser, locator_do_not_send_invoice,
                               "//em[contains(.,'DO NOT SEND INVOICE') and contains(.,'exclude')]")
        except Exception as ex:
            raise Exception("Click on 'DO NOT SEND INVOICE'. " + str(ex))

    def click_on_invoice_current_month(self):
        try:
            current_month = str(datetime.datetime.now().strftime('%h')).upper()
            current_year = str(datetime.datetime.now().strftime('%Y'))
            locator_current_month_invoice = \
                "//a[@class='name label-filter']//span[contains(.,'{} {}')]".format(current_month, current_year)
            check_locator = "//em[contains(.,'{} {}')]".format(current_month, current_year)
            com.click_and_wait(self.browser, locator_current_month_invoice, check_locator)
            check_locator = "//em[contains(.,'{} {}') and contains(.,'exclude')]".format(current_month, current_year)
            com.click_and_wait(self.browser, locator_current_month_invoice, check_locator)
        except Exception as ex:
            raise Exception("Click on INV of current month. '" + str(ex))

    def click_on_pr_amt_outstanding(self):
        try:
            locator_outstanding_patient_responsibility = "//div//ul//li//a[contains(.,'Outstanding Patient Responsibility')]"
            com.click_and_wait(self.browser, "//th//div//a[contains(text(),'PR Amt.')]",
                               locator_outstanding_patient_responsibility)
            self.browser.click_element_when_visible(locator_outstanding_patient_responsibility)
            com.wait_element(self.browser, '//*[@id="content"]/table/thead/tr/td/header/div/div/div/div/span/em[text() ="Patient Responsibility Status: Outstanding" ]')
        except Exception as ex:
            raise Exception("Select 'PR Amt.' -> 'Outstanding Patient Responsibility'. " + str(ex))

    def open_and_get_new_tab(self, link_url):
        self.browser.execute_javascript("window.open('"+link_url+"');")
        browser_tabs = self.browser.get_window_handles()
        return browser_tabs[len(browser_tabs)-1]

    def open_invoice_screen(self):
        try:
            fifth_day_of_current_month = datetime.datetime.utcnow().replace(day=5).strftime('%Y-%m-%d')
            lint_to_invoices = self.base_url + '#billingmanager/invoices/?startdate={}&enddate={}' \
                .format(fifth_day_of_current_month, fifth_day_of_current_month)
            browser_tab  = self.open_and_get_new_tab(lint_to_invoices)
            self.browser.switch_window(browser_tab)
        except Exception as ex:
            raise Exception("Open invoices screen." + str(ex))

    def open_contacts_screen(self):
        try:
            browser_tab = self.open_and_get_new_tab(self.base_url + '/#contacts')
            self.browser.switch_window(browser_tab)
        except Exception as ex:
            raise Exception("Open contacts screen." + str(ex))

    def mark_timesheets(self):
        try:
            self.click_checkbox_to_select_clients()
        except Exception as ex:
            raise Exception("Mark timesheets. " + str(ex))

    def get_clients_timesheets_selected(self, client_name: str, attempts: int = 3, timeout: int = 10):
        is_success = False
        count = 0
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                client_surname = self.get_surname(client_name)
                selected_client_timesheets_elems =self.browser.find_elements(
                    f'//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr/td[a[contains(text(), "{client_surname}")]]')

                return selected_client_timesheets_elems
            except Exception as ex:
                time.sleep(timeout)
                exception = ex
                count += 1

        if is_success is False:
            print("Error-Retry scope.The element was not appeared." + str(exception))
            raise exception

    def click_checkbox_to_select_clients(self,attempts: int = 3, timeout: int = 5):
        is_success = False
        count = 0
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                self.browser.click_element_when_visible(
                    '//*[@id="content"]/table/thead/tr/th/input[@data-bind="checked: listVm.allSelected"]')
                selected_checkbox = self.browser.find_elements(
                    '//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr[contains(@class, "selected")]')

                if len(selected_checkbox) > 0:
                    is_success = True
            except Exception as ex:
                time.sleep(timeout)
                exception = Exception("Selected clients")
                count += 1

        if is_success is False:
            print("Error-Retry scope.The element was not appeared." + str(exception))
            raise exception

    def bulk_generate_invoices(self):
        try:
            self.browser.click_element_when_visible('//*[@id="content"]/table/thead/tr/td/header/div/div/div/a[contains(text(),"Actions")]')
            self.browser.click_element_when_visible('//*[@id="content"]/table/thead/tr/td/header/div/div/div/ul/li/a[@data-bind = "click: bulkGenerateInvoices"]')

            if self.browser.is_element_visible('//button[contains(text(), "Yes, generate invoice *up to")]'):
                self.browser.click_element_when_visible('//button[contains(text(), "Yes, generate invoice *up to")]')

            self.browser.wait_until_element_is_visible('//div/a[text()="Patient Responsibility Invoice"]', 60)
            self.browser.click_element_when_visible('//div/a[text()="Patient Responsibility Invoice"]')
            self.browser.element_should_be_visible('//div/button/span[contains(@data-bind,"selectedBillTo()" )]')
        except Exception as ex:
            raise Exception("Bulk generate invoices. " + str(ex))

    def get_surname(self, name):
        client_name_splitted = name.split(" ")
        return client_name_splitted[len(client_name_splitted) - 1]

    # macro 3
    def update_invoice_line_item(self) -> (bool, bool):
        try:
            self.browser.click_button_when_visible('//td/div[contains(@data-bind, "selectedBillTo")]/child::button[span[@class="caret"]]')
            li_items = self.browser.find_elements('//ul[@data-bind = "foreach: billTo"]/child::li/a/span')

            is_private_invoice_item_exist_and_clicked = False
            is_secondary_payor_exist = False

            private_invoice_item = None
            for li_item in li_items:
                text_item = li_item.text
                if re.search(r"^S: ",text_item):
                    is_secondary_payor_exist = True
                if 'Private: Invoice' in text_item:
                    private_invoice_item = li_item

            if not private_invoice_item is None:
                private_invoice_item.click()
                is_private_invoice_item_exist_and_clicked = True

            return is_secondary_payor_exist, is_private_invoice_item_exist_and_clicked
        except Exception as ex:
            raise Exception("Update Invoice line item. " + str(ex))

    def select_private_invoice(self):
        try:
            self.browser.click_button_when_visible(
                '//td/div[contains(@data-bind, "selectedBillTo")]/child::button[span[@class="caret"]]')
            li_items = self.browser.find_elements('//ul[@data-bind = "foreach: billTo"]/child::li/a/span')

            for li_item in li_items:
                text_item = li_item.text
                if 'Private: Invoice' in text_item:
                    li_item.click()
                    break

        except Exception as ex:
            raise Exception("Unable to select 'Private Invoice' item. " + str(ex))



    def review_secondary_payor(self, client_name: str, client_id):
        try:
            id_trs_by_date_range = list()
            client_data = ClientSecondaryPayorModel()
            self.find_value_in_search_box(client_id,
                                             f'//em[@class="filter" and contains(text(), "{client_id}")]')
            if self.is_element_available('//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr', timeout=10):
                self.get_clients_timesheets_selected(client_name)
                client_data = self.open_contactcard_and_get_date_info(self.get_surname(client_name))
                id_trs_by_date_range = self.get_claims_id_by_date_range(client_data.date_effective_from,
                                                                        client_data.date_effective_to)
            return id_trs_by_date_range, client_data
        except Exception as ex:
            raise Exception("Review secondary payor. " + str(ex))

    def open_contactcard_and_get_date_info(self,client_surname ) -> ClientSecondaryPayorModel:
        try:
            self.browser.click_element_when_visible(f'//tr/td/a[contains(text(), "{client_surname}")]')
            self.browser.wait_until_element_is_visible('//div/a[contains(@class, "contactCardTitle")]', '10 seconds')

            self.browser.click_element_when_visible('//div/a[contains(@class, "contactCardTitle")]')
            self.browser.wait_until_element_is_visible('//div/ul/li/a[text()="Payors"]', '10 seconds')

            self.browser.click_element_when_visible('//div/ul/li/a[text()="Payors"]')

            if not self.is_element_available('//div/a/span[contains(text(),"Secondary")]', timeout=10):
                self.browser.click_element_when_visible('//div/div[contains(@class,"module-actions")]/a[@title="Show/Hide More"]')

            self.browser.wait_until_element_is_visible('//div/a/span[contains(text(),"Secondary")]', '10 seconds')

            self.browser.click_element_when_visible('//div/a/span[contains(text(),"Secondary")]')
            self.browser.wait_until_element_is_visible('//div[contains(text(),"Effective from:")]/span', '30 seconds')

            client = ClientSecondaryPayorModel()
            client.secondary_payor_info = self.browser.find_element('//div/a/span[contains(text(),"Secondary")]').text
            client.date_effective_from = self.browser.find_element('//div[contains(text(),"Effective from:")]/span').text
            client.date_effective_to = self.browser.find_element('//div[contains(text(),"Effective to:")]/span').text

            if client.date_effective_to.strip() == '':
                client.date_effective_to = datetime.datetime.utcnow().strftime("%m/%d/%Y")

            return client
        except Exception as ex:
            raise Exception("Open contactcard and get date info. " + str(ex))

    def get_claims_id_by_date_range(self,start_date: str, end_date: str) -> list:
        try:
            claims_by_date_range = list()
            start_date = self.convert_date(start_date)
            end_date = self.convert_date(end_date)
            self.set_date_range(start_date, end_date)
            if self.is_element_available('//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr',timeout=10):
                claim_trs = self.browser.find_elements(
                    '//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr')
                for claim_elem in claim_trs:
                    claims_by_date_range.append(claim_elem.get_attribute("id"))

            return claims_by_date_range
        except Exception as ex:
            raise Exception("Get claims id by date range. " + str(ex))

    def non_secondary_madicaid_process(self, id_trs_by_date_range ) -> bool:
        try:
            time.sleep(2)
            is_need_add_label_2ndrv = False
            is_need_generate_edited_patient_responsibility_invoice = False
            count_with_code_oa23 = 0
            for row_id in id_trs_by_date_range:
                if not self.check_code_oa23(row_id):
                    self.browser.click_element_when_visible(
                        f'//tr[@id="{row_id}"]/child::td/input[@type="checkbox"]')
                    is_need_add_label_2ndrv = True
                else:
                    count_with_code_oa23+=1

            if count_with_code_oa23 > 0:
                com.log_message(f"{count_with_code_oa23} - found claims with code: OA23")

            if is_need_add_label_2ndrv:
                self.add_label("2NDRV")
                is_need_generate_edited_patient_responsibility_invoice =True

            return is_need_generate_edited_patient_responsibility_invoice
        except Exception as ex:
            raise Exception("Non secondary madicaid process. " + str(ex))

    def check_code_oa23(self, row_id) -> bool:
        try:
            is_code_exist = False
            com.wait_element(self.browser, f'//tr[@id="{row_id}"]/child::td/a/i[@class="far fa-fw fa-plus"]')

            if not self.browser.is_element_visible(f'//tr[@id="{row_id}"]/child::td/a/i[@class="far fa-fw fa-plus"]'):
                self.browser.scroll_element_into_view(f'//tr[@id="{row_id}"]/child::td/a/i[@class="far fa-fw fa-plus"]')

            self.browser.click_element_when_visible(f'//tr[@id="{row_id}"]/child::td/a/i[@class="far fa-fw fa-plus"]')
            com.wait_element(self.browser,
                             f'//tr[@id="{row_id}"]/following-sibling::tr/td[b[text()="Date"]]/following-sibling::td[b[text()="Payor"]]')
            secondary_payor_rows = self.browser.find_elements('//tr[td/span[@data-title-bind ="payor" and contains(text(),"S: ")]]')
            if len(secondary_payor_rows) > 0:
                row_text: str = secondary_payor_rows[len(secondary_payor_rows)-1].text
                if "oa23" in row_text.lower():
                    is_code_exist = True

            com.wait_element(self.browser,
                             f'//tr[@id="{row_id}"]/child::td/a/i[@class="far fa-fw fa-minus"]')
            self.browser.click_element_when_visible(f'//tr[@id="{row_id}"]/child::td/a/i[@class="far fa-fw fa-minus"]')
            time.sleep(2)
            return is_code_exist
        except Exception as ex:
            raise Exception("Check code oa23. " + str(ex))

    def set_date_range(self, start_date, end_date):
        try:
            link = self.browser.location
            old_start_date: str = re.findall(r"startdate=(?:[0-9]{2})?[0-9]{2}-[0-3]?[0-9]-[0-3]?[0-9]", link)[0].replace(
                "startdate=", "")
            old_end_date: str = re.findall(r"enddate=(?:[0-9]{2})?[0-9]{2}-[0-3]?[0-9]-[0-3]?[0-9]", link)[0].replace(
                "enddate=", "")

            new_link = link.replace(old_start_date, start_date).replace(old_end_date, end_date)
            self.browser.go_to(new_link)

            start_date_as_date = datetime.datetime.strptime(start_date,"%Y-%m-%d")
            end_date_as_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

            start_date_str: str = f'{start_date_as_date.strftime("%b")} {start_date_as_date.day}'
            end_date_str: str =f'{end_date_as_date.strftime("%b")} {end_date_as_date.day}'

            com.wait_element(self.browser, f'//div[contains(@data-bind,"dateRange")]/i[@class="far fa-calendar-alt fa-fw"]/following-sibling::span[contains(text(),"{start_date_str}") and contains(text(),"{end_date_str}")]')
        except Exception as ex:
            raise Exception("Set date range. " + str(ex))

    @staticmethod
    def convert_date(date_str) -> str:
        date_format = datetime.datetime.strptime(date_str, "%m/%d/%Y")
        return date_format.strftime("%Y-%m-%d")

    def add_label(self, label_value):
        try:
            self.browser.wait_and_click_button('//button[contains(., "Label selected")]')
            com.wait_element(self.browser, '//h2[text() = "Bulk Apply Labels"]')

            self.browser.input_text_when_element_is_visible('//*[@id="s2id_autogen4"]', label_value)
            com.wait_element(self.browser,f'//*[@id="select2-drop"]/ul/li/div[contains(., "{label_value}")]')

            self.browser.click_element_when_visible(f'//*[@id="select2-drop"]/ul/li/div[contains(., "{label_value}")]')
            com.wait_element(self.browser,f'//*[@id="s2id_autogen3"]/ul[li/div[contains(., "{label_value}")]]')

            self.browser.wait_and_click_button('//button[contains(.,"Apply Label Changes")]')
            self.browser.wait_until_page_does_not_contain('//h2[text() = "Bulk Apply Labels"]')

        except Exception as ex:
            raise Exception("Add label. " + str(ex))

    def secondary_madicaid_process(self):
        try:
            self.browser.click_element_when_visible(
                '//*[@id="content"]/table/thead/tr/th/input[@data-bind="checked: listVm.allSelected"]')

            com.wait_element(self.browser, '//div/a[contains(text(), "Actions")]')

            self.browser.click_element_when_visible('//div/a[contains(text(), "Actions")]')
            com.wait_element(self.browser, '//ul/li/a[contains(text(), "Apply Patient Responsibility")]')

            self.browser.click_element_when_visible('//ul/li/a[contains(text(), "Apply Patient Responsibility")]')
            com.wait_element(self.browser, '//*[@id="copay-payors"]/form/div/div/select')

            # Payor tab
            self.browser.click_element_when_visible('//*[@id="copay-payors"]/form/div/div/select')
            item_locator = '//*[@id="copay-payors"]/form/div/div/select/option[contains(text(), "Secondary: ")]'
            com.wait_element(self.browser,item_locator)
            self.browser.click_element_when_visible(item_locator)

            self.browser.click_element_when_visible('//*[@id="copay-payors"]/form/div/label[text() = "Payors"]')

            self.browser.click_element_when_visible(
                '//*[@id="billing-copay-widget"]/div/div/div/ul/li/a[text() ="Manual"]')
            com.wait_element(self.browser,
                             '//*[@id="copay-manual"]/form/div/table/thead/tr/child::th[text() ="Patient responsibility"]')

            # Manual tab
            input_elems = self.browser.find_elements('//*[@id="copay-manual"]/form/div/table/tbody/tr/td/div/input')

            for index in range(len(input_elems)):
                self.browser.input_text_when_element_is_visible(
                    f'//*[@id="copay-manual"]/form/div/table/tbody/tr[{str(index + 1)}]/td/div/input', "0")

            if self.is_element_available(
                    '//*[@id="copay-manual"]/form/button[contains(text(),"Manually update")]', timeout=20):
                self.browser.click_element_when_visible(
                    '//*[@id="copay-manual"]/form/button[contains(text(),"Manually update")]')

        except Exception as ex:
            raise Exception("Secondary madicaid process. " + str(ex))

    def generate_edited_patient_responsibility_invoice(self, client_name) -> bool:
        try:
            is_next_step_lockbox = False
            self.browser.click_element_when_visible('//div/a[text() = "Choose a Different Type"]/following-sibling::a[text() = "Cancel"]')
            com.wait_element(self.browser, '//*[@id="s2id_autogen2_search" and not(@placeholder="")]')
            self.browser.reload_page()
            claim_trs = self.browser.find_elements(
                '//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr')

            if len(claim_trs) > 0:
                is_next_step_lockbox = True
                self.mark_timesheets()
                self.bulk_generate_invoices()

            return is_next_step_lockbox

        except Exception as ex:
            raise Exception("Generate edited patient responsibility invoice. " + str(ex))

    def set_filter_by_2ndrv(self):
        try:
            if not self.browser.is_element_visible("//em[contains(.,'2NDRV') and contains(.,'exclude')]"):
                self.find_value_in_search_box("2NDRV","//em[contains(text(),'2NDRV')]")

                self.browser.click_element_when_visible('//span[em[contains(text(),"2NDRV")]]/a[b[@class="caret no-margin"]]')
                time.sleep(2)
                com.wait_element(self.browser, '//span[em[contains(text(),"2NDRV")]]/ul/li[a[@data-click="excludeItem"]]')

                self.browser.click_element_when_visible(
                    '//span[em[contains(text(),"2NDRV")]]/ul/li[a[@data-click="excludeItem"]]')
                com.wait_element(self.browser, "//em[contains(text(),'exclude') and contains(text(), '2NDRV')]")
                time.sleep(2)
        except Exception as ex:
            raise Exception("Set filter by 2NDRV. " + str(ex))

    def lockbox(self):
        try:
            self.browser.click_element_when_visible('//table/tbody/tr/td[3]/div/button[span[text()="Choose..."]]')
            com.wait_element(self.browser, '//ul/li[a/span[contains(text(), "Lockbox")]]')
            self.browser.click_element_when_visible('//ul/li[a/span[contains(text(), "Lockbox")]]')
            com.wait_element(self.browser, '//table/tbody/tr/td[3]/div/button[span[contains(text(), "Lockbox")]]')
        except Exception as ex:
            raise Exception("Lockbox. " + str(ex))

    def set_duedate(self):
        try:
            self.browser.click_element_when_visible('//input[@data-bind="datepicker: dueDate"]')
            date_str = self.calk_need_date_and_convert_to_str()
            self.browser.input_text_when_element_is_visible('//input[@data-bind="datepicker: dueDate"]',date_str)
            self.browser.click_element_when_visible('//thead/tr/th/span[text()="Due date"]')
        except Exception as ex:
            raise Exception("Set duedate. " + str(ex))

    @staticmethod
    def calk_need_date_and_convert_to_str() -> str:
        next_month = datetime.datetime.now().month + 1
        year = datetime.datetime.now().year
        fifth_day = 5
        fifth_day_of_next_month = datetime.date(year=year, month=next_month, day=fifth_day)
        day_of_week = fifth_day_of_next_month.weekday()
        need_day = CentralReach.calculate_day_by_week_day(day_of_week, fifth_day)
        new_date = datetime.date(year=year, month=next_month, day=need_day)
        return new_date.strftime("%m/%d/%Y")

    @staticmethod
    def calculate_day_by_week_day(weekday, day):
        if weekday == 0:
            return day + 4
        elif weekday == 1:
            return day + 3
        elif weekday == 2:
            return day + 2
        elif weekday == 3:
            return day + 1
        elif weekday == 4:
            return day
        elif weekday == 5:
            return day + 6
        elif weekday == 6:
            return day + 5

    def update_private_invoices(self,client_id):
        try:
            self.go_to_by_link(self.base_url + f'/#contacts/details/?id={client_id}&mode=profile&edit=payors')
            com.wait_element(self.browser, '//ul/li/a[@data-toggle="tab"][text()="Other"]')

            self.browser.click_element_when_visible(
                '//ul/li/a[@data-toggle="tab"][text()="Other"]')

            self.browser.click_element_when_visible('//div/a[contains(text(),"Add New")]')
            com.wait_element(self.browser, '//ul/li/a[contains(text(),"Other") and @data-hash]')

            self.browser.click_element_when_visible('//ul/li/a[contains(text(),"Other") and @data-hash]')
            com.wait_element(self.browser, '//*[@id="accountInsuranceEditPane"]/div/ul/li/a/span[.="Subscriber"]')

            self.browser.click_element_when_visible(
                '//*[@id="accountInsuranceEditPane"]/div/ul/li/a/span[.="Subscriber"]')
            com.wait_element(self.browser,
                             '//*[@id="patient-subscriber"]/form/div/div/span[@class="error"]/following-sibling::a/i[@class="fa fa-fw fa-sync txt-lg"]')

            self.browser.click_element_when_visible(
                '//*[@id="patient-subscriber"]/form/div/div/span[@class="error"]/following-sibling::a/i[@class="fa fa-fw fa-sync txt-lg"]')
            com.wait_element(self.browser,
                             '//*[@id="patient-subscriber"]/form/div[2]/div/input[@class="form-control block" ]')

            if self.is_element_available('//button[@data-click="save"]', timeout=20):
                self.browser.click_element_when_visible('//button[@data-click="save"]')

        except Exception as ex:
            raise Exception("Update private invoice. " + str(ex))

    def find_value_in_search_box(self, value_str: str, expected_locator):
        attempts = 3
        is_success = False
        count = 0
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                search_element = self.browser.find_element('//*[@id="s2id_autogen2_search" and not(@placeholder="")]')
                time.sleep(2)
                search_element.send_keys(value_str)
                time.sleep(2)
                search_element.send_keys(Keys.ENTER)
                time.sleep(2)
                com.wait_element(self.browser, expected_locator)
                self.browser.reload_page()
                is_success =True
            except Exception as ex:
                time.sleep(3)
                exception = ex
                count += 1

        if is_success is False:
            print("Error-Retry scope.The element was not appeared." + str(exception))
            raise exception

    def remove_filter_2ndrv(self):
        try:
            locator = '//em[contains(text(),"2NDRV") and contains(text(),"exclude")]/following-sibling::a[@class="remove"]'
            if self.browser.is_element_visible(locator):
                self.browser.click_element_when_visible(locator)
        except Exception as ex:
            raise Exception("Remove filter 2NDRV. " + str(ex))


    # MACRO 4
    def generate_invoices(self):
        try:
            com.wait_element(self.browser, "//a[contains(text(),'Bulk-Generate')]")
            self.browser.click_element_when_visible("//a[contains(text(),'Bulk-Generate')]")

            com.wait_element(self.browser, '//a[contains(text(),"Click here to print your invoices")]')
            self.browser.click_element_when_visible('//a[contains(text(),"Click here to print your invoices")]')

            self.go_to_new_tab('//button[contains(text(),"Generate PDF")]')
            com.click_and_wait(self.browser, '//button[contains(text(),"Generate PDF")]',
                               '//button[contains(text(), "Download All")]')

            try:
                com.click_and_wait(self.browser, '//button[contains(text(), "Download All")]','//button/span[contains(text(), "Done")]', timeout=1000)
            except:
                pass

            self.close_all_tabs_except_first()
            com.wait_element(self.browser,
                         '//a[contains(text(),"Click here to print your invoices")]/following-sibling::a[text() = "Back to billing" and @data-bind="click: cancel"]')
            self.browser.click_element_when_visible(
            '//a[contains(text(),"Click here to print your invoices")]/following-sibling::a[text() = "Back to billing" and @data-bind="click: cancel"]')

            com.wait_element(self.browser, '//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr')
        except Exception as ex:
            raise Exception(f"Generate invoices. "+ str(ex))

    def close_all_tabs_except_first(self):
        try:
            browser_tabs = self.browser.get_window_handles()
            for i in range(len(browser_tabs)):
                if i > 0:
                    self.browser.switch_window(browser_tabs[i])
                    self.browser.close_window()

            browser_tabs = self.browser.get_window_handles()
            self.browser.switch_window(browser_tabs[0])
        except Exception as ex:
            raise Exception("Close all tabs except 1-st. " + str(ex))

    def go_to_new_tab(self, locator, timeout=5):
        try:
            is_need_tab_exist = False
            tabs = self.browser.get_window_handles()
            for i in range(len(tabs)):
                if i > 0:
                    self.browser.switch_window(tabs[i])
                    if self.is_element_available(locator, timeout=timeout):
                        is_need_tab_exist = True
                    else:
                        self.browser.close_window()

            if not is_need_tab_exist:
                raise Exception(f"Tab with locator: '{locator}' was not found")

        except Exception as ex:
            raise Exception("Go to new_tab. " + str(ex))

    def closeout_invoices(self):
        is_all_timesheets_set_label =False
        while not is_all_timesheets_set_label:
            if not self.browser.is_element_visible(
                    '//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr[contains(@class,"row-item") and contains(@class,"selected")]'):
                self.browser.click_element_when_visible(
                    '//*[@id="content"]/table/thead/tr/th/input[@data-bind="checked: listVm.allSelected"]')
                com.wait_element(self.browser,
                                 '//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr[contains(@class,"row-item") and contains(@class,"selected")]')

            date_str = f"{str(datetime.datetime.now().strftime('%h')).upper()} {str(datetime.datetime.now().strftime('%Y'))}"
            label_inv_d_cur_month_year = f"INV'D {date_str}"

            self.add_label(label_inv_d_cur_month_year)

            # switch from exclude to include
            self.include_cur_month_label()

            # switch from include to exclude
            self.exclude_cur_month_label()

            is_all_timesheets_set_label = self.is_element_available(
                "//td/header/div[contains(@class,'alert alert-danger') and text()='No results matched your keywords, filters, or date range']",timeout=30)


    def include_cur_month_label(self):
        url_with_removed_exlude = self.browser.location.replace("-"+self.id_label_inv_cur_month,"")
        new_url = url_with_removed_exlude + "&billingLabelIdIncluded="+self.id_label_inv_cur_month
        self.go_to_by_link(new_url)

    def exclude_cur_month_label(self):
        url_with_removed_include = self.browser.location.replace("&billingLabelIdIncluded=" + self.id_label_inv_cur_month, "")
        new_url = url_with_removed_include.replace("&billingLabelIdExcluded=",f"&billingLabelIdExcluded={self.id_label_inv_cur_month}-")
        self.go_to_by_link(new_url)

    def generate_contacts_clients_files(self):
        return self.export_csv_contacts("Clients", self.base_url + '/#contacts/?filter=clients')

    def generate_contacts_clients_inactive_files(self):
        return self.export_csv_contacts("Inactive clients", self.base_url + '/#contacts/?filter=clientsinactive')

    def export_csv_contacts(self, file_type, link_url):
        self.go_to_by_link(link_url)
        file_name = f'Contacts_{file_type}'
        try:
            self.browser.click_element_when_visible('//button[i[contains(@class,"fa-cloud-download")]]')
            self.browser.click_element_when_visible(
                '//button[i[contains(@class,"fa-cloud-download")]]/following-sibling::ul/li[a[text()="CSV"]]')
            com.wait_element(self.browser, '//a[@type="button"and text()="Go To Files"]')

            if self.is_element_available('//div[contains(text(), "Your export has been started")]', timeout=5):
                count = 0
                attempts = 3
                is_success = False
                timeout = 5
                exception: Exception = Exception()
                while (count < attempts) and (is_success is False):
                    try:
                        self.browser.reload_page()

                        self.browser.click_element_when_visible('//button[i[contains(@class,"fa-cloud-download")]]')
                        self.browser.click_element_when_visible(
                            '//button[i[contains(@class,"fa-cloud-download")]]/following-sibling::ul/li[a[text()="CSV"]]')
                        com.wait_element(self.browser, '//*[@type="button"and text()="Go To Files"]')

                        com.wait_element(self.browser, '//h4/a[i[@class="fa fa-download"] and text()="Download"]', timeout=timeout)
                        is_success = True
                    except Exception as ex:
                        exception = Exception("Download icon was not exist")
                        count += 1

                if not is_success:
                    raise exception

            com.wait_element(self.browser,'//h4/a[i[@class="fa fa-download"] and text()="Download"]', timeout=20)
            self.browser.click_element_when_visible('//h4/a[i[@class="fa fa-download"] and text()="Download"]')
            downloaded_path_to_file = com.get_downloaded_file_path(path_to_temp=os.path.abspath("temp/cr"),
                                                                   extension=".csv",
                                                                   error_message="file not exist")
            path_to_file = com.move_file_to_temp(path_to_file=downloaded_path_to_file,
                                                 new_file_name=file_name + ".csv")
            self.browser.click_element_when_visible('//button[@type="button"and text()="Close"]')

            com.log_message(f"'{file_name}' file exported and download")
            return path_to_file
        except Exception as ex:
            raise Exception(f"Unable to export '{file_name}'. "+str(ex), 'ERROR')

    def export_cvs_billing_by_date_range(self, start_date, end_date):
        try:
            self.set_date_range(start_date, end_date)
            self.browser.reload_page()
            file_name_start_date: str = datetime.datetime.strptime(start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
            file_name_end_date: str = datetime.datetime.strptime(end_date, "%Y-%m-%d").strftime("%m/%d/%Y")
            file_name = f"Billing from {file_name_start_date} to {file_name_end_date}"
            com.log_message(f"'{file_name}'", 'INFO')
            if not self.is_element_available(
                    '//td/header/div[contains(@class,"alert-danger") and contains(text(), "No results matched")]',
                    timeout=20):
                self.browser.click_element_when_visible('//button[i[contains(@class,"fa-cloud-download")]]')
                self.browser.click_element_when_visible(
                    '//button[i[contains(@class,"fa-cloud-download")]]/following-sibling::ul/li/div/div/a[@data-value="standard_csv"]')
                com.wait_element(self.browser,
                                 '//a[@type="button"and text()="Go To Files"]/following-sibling::button[@type="button"and text()="Close"]')

                if self.is_element_available('//div[contains(text(), "Your export has been started")]', timeout=5):
                    count = 0
                    attempts = 3
                    is_success = False
                    timeout = 5
                    exception: Exception = Exception()
                    while (count < attempts) and (is_success is False):
                        try:
                            self.browser.reload_page()

                            self.browser.click_element_when_visible('//button[i[contains(@class,"fa-cloud-download")]]')
                            self.browser.click_element_when_visible(
                                '//button[i[contains(@class,"fa-cloud-download")]]/following-sibling::ul/li/div/div/a[@data-value="standard_csv"]')
                            com.wait_element(self.browser,
                                             '//a[@type="button"and text()="Go To Files"]/following-sibling::button[@type="button"and text()="Close"]')

                            com.wait_element(self.browser, '//h4/a[i[@class="fa fa-download"] and text()="Download"]',
                                             timeout=timeout)
                            is_success = True
                        except Exception as ex:
                            exception = Exception("Download icon was not exist")
                            count += 1

                    if not is_success:
                        raise exception

                com.wait_element(self.browser, '//h4/a[i[@class="fa fa-download"] and text()="Download"]', timeout=20)
                self.browser.click_element_when_visible('//h4/a[i[@class="fa fa-download"] and text()="Download"]')
                downloaded_path_to_file = com.get_downloaded_file_path(path_to_temp=os.path.abspath("temp/cr"),
                                                                       extension=".csv",
                                                                       error_message="file not exist")
                path_to_file = com.move_file_to_temp(path_to_file=downloaded_path_to_file,
                                                     new_file_name=file_name + ".csv")
                self.browser.click_element_when_visible(
                    '//a[@type="button"and text()="Go To Files"]/following-sibling::button[@type="button"and text()="Close"]')
                self.browser.wait_until_page_does_not_contain(
                    '//a[@type="button"and text()="Go To Files"]/following-sibling::button[@type="button"and text()="Close"]')

                com.log_message(f"File exported and download")
                self.downloaded_billing_csvs[file_name] = path_to_file
            else:
                raise Exception("No results matched your keywords, filters, or date range")
        except Exception as ex:
            com.log_message(f"Unable to export file. " + str(ex), 'ERROR')

    def generate_billing_reports_files(self):
        self.go_to_by_link(self.base_url+"#billingmanager/billing/?sort=date")

        #set labals and filters
        self.browser.click_element_when_visible("//li/a[text()='Labels']")
        self.check_and_open_patient_invoices()
        self.set_invoices_current_month_without_exclude()

        self.download_reports()


    def download_reports(self, start_year = 2016):
        is_last_date_range_iteration = False
        year_counter = 0

        cur_year = datetime.datetime.now().year
        previous_month = self.get_last_day_of_previous_month().strftime("%m")
        last_day_of_previous_month = self.get_last_day_of_previous_month().strftime("%d")
        cur_month = datetime.datetime.now().month

        while (not is_last_date_range_iteration):
            year = start_year + year_counter
            if year < cur_year:
                self.export_cvs_billing_by_date_range(f"{year}-01-01", f"{year}-06-30")
                self.export_cvs_billing_by_date_range(f"{year}-07-01", f"{year}-12-31")
            elif year == cur_year:
                if cur_month > 1 and cur_month <= 7:
                    self.export_cvs_billing_by_date_range(f"{year}-01-01",
                                                          f"{year}-{previous_month}-{last_day_of_previous_month}")
                elif cur_month > 7:
                    self.export_cvs_billing_by_date_range(f"{year}-01-01", f"{year}-06-30")
                    self.export_cvs_billing_by_date_range(f"{year}-01-01",
                                                          f"{year}-{previous_month}-{last_day_of_previous_month}")
                is_last_date_range_iteration = True
            # increment
            year_counter = year_counter + 1

        if len(self.downloaded_billing_csvs) == 0:
            com.log_message(f"'Billing*.csv' files were not exported", 'ERROR')
        else:
            com.log_message(f"{len(self.downloaded_billing_csvs)} - 'Billing*.csv' files were exported")


    def set_invoices_current_month_without_exclude(self):
        current_month = str(datetime.datetime.now().strftime('%h')).upper()
        current_year = str(datetime.datetime.now().strftime('%Y'))
        locator_current_month_invoice = \
            "//a[@class='name label-filter']//span[contains(.,'{} {}')]".format(current_month, current_year)
        check_locator = "//em[contains(.,'{} {}')]".format(current_month, current_year)
        com.click_and_wait(self.browser, locator_current_month_invoice, check_locator)

    def remove_element(self, locator):
        element = self.browser.find_element(locator)
        self.browser.driver.execute_script("""
               var element = arguments[0];
               element.parentNode.removeChild(element);
               """, element)

    def download_file(self):
        self.go_to_new_tab('//button[@data-click="getDownloadUrl"]')
        file_name = self.browser.find_element('//h2[@data-bind="text: name"]').text + datetime.datetime.utcnow().strftime("_%I%M%S%f")
        self.browser.click_element_when_visible('//button[@data-click="getDownloadUrl"]')
        com.wait_element(self.browser,
                         '//div/h4[contains(text(),"Download version:")]/following-sibling::a[contains(text(), "https://")]')
        self.browser.click_element_when_visible(
            '//div/h4[contains(text(),"Download version:")]/following-sibling::a[contains(text(), "https://")]')
        downloaded_path_to_file = com.get_downloaded_file_path(path_to_temp=os.path.abspath("temp/cr"), extension=".csv",
                                                    error_message="file not exist")
        path_to_file = com.move_file_to_temp(path_to_file=downloaded_path_to_file, new_file_name= file_name+ ".csv")
        self.close_all_tabs_except_first()
        return file_name, path_to_file

    def get_data_from_cr(self, client_id):
        data = None
        count =0
        attempts =3
        is_success = False
        timeout = 5
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                self.go_to_by_link(self.base_url+f"#contacts/details/?id={client_id}&mode=profile&edit=payors&edit-payor")
                self.browser.click_element_when_visible(
                    '//ul/li/a[@data-toggle="tab"][text()="Other"]')
                elements = self.browser.find_elements("//div/a/i[@class='fas fa-pencil']")

                data = ColumnsWithPayorsData()
                if len(elements)> 0 :
                    data = self.scrap_data()
                else:
                    data = None
                is_success = True
            except Exception as ex:
                self.close_browser()
                self.login_to_central_reach()
                time.sleep(timeout)
                exception = ex
                count += 1

        return data

    def scrap_data(self, index=1):
        payor_data = ColumnsWithPayorsData()
        name = self.browser.find_element(f'//div[{index}]/div/div/b[text() = "Name"]//following-sibling::div/span').text
        address = self.browser.find_element(
            f'//div[{index}]/div/div/b[text() = "Address"]//following-sibling::div').text
        payor_data.mail_to_first_name = name.split(' ')[0]
        payor_data.mail_to_last_name = name.split(' ')[1]
        payor_data.mail_to_address_first = address
        return payor_data

    def restart_page_after_update_private_invoice(self):
        try:
            self.browser.reload_page()
            com.wait_element(self.browser, '//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr')
        except Exception as ex:
            raise Exception("Error - Restart page after update 'Private Invoice'. "+str(ex))

    def select_client(self, client_name=''):
        is_success = False
        count = 0
        attempts = 4
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                client_data = ClientModel()
                self.browser.reload_page()
                com.click_and_wait(self.browser, "//tr/th[div/a/span[text()='Client']]//child::a/i",
                                   "//*[@id='clientsFilterList']/div/div/span[text() = 'clients']", 400)
                is_last_client = False
                clients = self.browser.find_elements(
                    '//div[@id="clientsFilterList"]/div/div/ul[@class="list-unstyled"]/li')
                if len(clients) == 1:
                    is_last_client = True

                if client_name:
                    client_name = self.browser.find_element(
                        f'//div[@id="clientsFilterList"]/div/div/ul[@class="list-unstyled"]/li/a/span[text()="{client_name}"]').text
                else:
                    client_name = self.browser.find_element(
                        '//div[@id="clientsFilterList"]/div/div/ul[@class="list-unstyled"]/li[1]/a/span').text

                com.click_and_wait(self.browser,
                                   '//div[@id="clientsFilterList"]/div/div/ul[@class="list-unstyled"]/li[1]',
                                   f'//div[@class="filters search-filters"]/div/span/em[contains(.,"{self.get_surname(client_name)}")]')

                text_from_label: str = self.browser.find_element(
                    f'//div[@class="filters search-filters"]/div/span/em[contains(.,"{self.get_surname(client_name)}")]').text
                client_id = re.search(r"\d+", text_from_label)[0]
                self.browser.reload_page()
                client_data.id = client_id
                client_data.name = client_name
                return client_data, is_last_client

            except Exception as ex:
                time.sleep(5)
                exception = Exception("Error - Select client. " + str(ex))
                count += 1

        if is_success is False:
            raise exception

    def add_errors_label(self, client_id):
        is_success = False
        count = 0
        attempts = 4
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                self.find_value_in_search_box(client_id,
                                              f'//em[@class="filter" and contains(text(), "{client_id}")]')

                if not self.browser.is_element_visible(
                        '//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr[contains(@class,"row-item") and contains(@class,"selected")]'):
                    self.browser.click_element_when_visible(
                        '//*[@id="content"]/table/thead/tr/th/input[@data-bind="checked: listVm.allSelected"]')
                    com.wait_element(self.browser,
                                     '//*[@id="content"]/table/tbody[contains(@data-bind, "crLabelWidget")]//child::tr[contains(@class,"row-item") and contains(@class,"selected")]')

                self.add_label(self.error_label_name)
                self.browser.reload_page()
                is_success = True
            except Exception as ex:
                time.sleep(3)
                exception = Exception("Unable to add temp error label. " + str(ex))
                count += 1

        if is_success is False:
            raise exception


    def remove_filter_by_client(self, client_id):
        try:
            com.wait_element(self.browser,
                             f'//div[@class="filters search-filters"]/div/span/em[contains(.,"{client_id}")]/following-sibling::a[@title="Remove filter"]')
            self.browser.click_element_when_visible(
                f'//div[@class="filters search-filters"]/div/span/em[contains(.,"{client_id}")]/following-sibling::a[@title="Remove filter"]')
            self.browser.wait_until_page_does_not_contain(
                f'//div[@class="filters search-filters"]/div/span/em[contains(.,"{client_id}")]/following-sibling::a[@title="Remove filter"]')
            self.browser.reload_page()
            com.wait_element(self.browser,"//em[contains(.,'DO NOT SEND INVOICE') and contains(.,'exclude')]", timeout=360)
        except Exception as ex:
            raise Exception("Remove filter by client. "+str(ex))

    def check_is_need_reload_page(self):
        is_success = False
        count = 0
        attempts = 4
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                if not self.is_element_available(
                        '//*[@id="content"]/table/thead/tr/td/header/div/div/div/div/span/em[text() ="Patient Responsibility Status: Outstanding" ]',
                        120):
                    self.browser.reload_page()

                com.wait_element(self.browser, '//*[@id="content"]/table/thead/tr/td/header/div/div/div/div/span/em[text() ="Patient Responsibility Status: Outstanding" ]', 120)
                is_success = True
            except Exception as ex:
                time.sleep(3)
                exception = Exception("msg. " + str(ex))
                count += 1

        if is_success is False:
            raise exception

        if not self.is_element_available('//*[@id="content"]/table/thead/tr/td/header/div/div/div/div/span/em[text() ="Patient Responsibility Status: Outstanding" ]', 120):
            self.browser.reload_page()




