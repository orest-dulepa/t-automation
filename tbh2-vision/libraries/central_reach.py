from RPA.Browser.Selenium import Selenium
from RPA.Tables import Table
from libraries import common
from urllib.parse import urlparse
import datetime
import time
import os
import shutil
import re
from libraries.excel import ExcelInterface
from libraries.waystar import WayStar
from libraries.models.insurance import Insurance
from libraries.models.provider import Provider
from libraries.models.client import Client
from libraries.models.timesheet import Timesheet
import traceback


class CentralReach:
    filter_secondary_claims = 'Secondary Claims'
    list_of_non_insurance = ['None', 'School District', 'California Regional Center', 'Private Pay']

    def __init__(self, credentials: dict):
        self.browser: Selenium = Selenium()
        self.browser.timeout = 30
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.base_url: str = self.get_base_url()
        self.login_to_central_reach()

        self.start_date: datetime = None
        self.end_date: datetime = None

        self.mapping: ExcelInterface = None

        self.headers_index: dict = {}
        self.headers_index_claims: dict = {}

        self.domo_mapping_file = None
        self.domo_mapping_site = None

        self.crosswalk_guide: dict = {}
        self.crosswalk_guide_populated: dict = {}

        self.waystar: WayStar = None
        self.trump_site_list: list or None = None

    def get_base_url(self):
        parsed_uri = urlparse(self.url)
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

    def login_to_central_reach(self):
        self.browser.close_browser()
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
                common.wait_element(self.browser, "//input[@type='password']", is_need_screen=False, timeout=10)
                if self.browser.does_page_contain_element("//p[text()='Scheduled Maintenance']"):
                    if self.browser.find_element("//p[text()='Scheduled Maintenance']").is_displayed():
                        common.log_message("Logging into CentralReach failed. Scheduled Maintenance.".format(count),
                                           'ERROR')
                        self.browser.capture_page_screenshot(
                            os.path.join(
                                os.environ.get("ROBOT_ROOT", os.getcwd()),
                                'output',
                                'Centralreach_scheduled_maintenance.png')
                        )
                        return
                common.wait_element(self.browser, "//input[@type='password']", is_need_screen=False)
                self.browser.input_text_when_element_is_visible("//input[@type='text']", self.login)
                self.browser.input_text_when_element_is_visible("//input[@type='password']", self.password)
                self.browser.click_button_when_visible("//button[@class='btn']")
                if self.browser.does_page_contain_element('//div[@class="loginError"]/div[text()="There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support"]'):
                    elem = self.browser.find_element('//div[@class="loginError"]/div[text()="There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support"]')
                    if elem.is_displayed():
                        common.log_message("Logging into CentralReach failed. There was an unexpected problem signing in.".format(count), 'ERROR')
                        raise Exception("There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support")
                common.wait_element_and_refresh(self.browser, "//span[text()='Favorites']", is_need_screen=False)
                self.is_site_available = self.browser.does_page_contain_element("//span[text()='Favorites']")
            except Exception as ex:
                common.log_message("Logging into CentralReach. Attempt #{} failed".format(count), 'ERROR')
                print(str(ex))
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

    @staticmethod
    def calculate_date():
        start_date = datetime.datetime.strptime('9/1/2019', '%m/%d/%Y')
        end_date = datetime.datetime.utcnow() + datetime.timedelta(days=-45)

        print('Start date: {}. End date: {}'.format(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        return start_date, end_date

    def apply_filter(self, filter_name: str, additional_params='', sort_by_client=False):
        # Go to billing page
        self.browser.go_to(self.base_url + '#billingmanager/billing/?startdate={}&enddate={}'.format(
            self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d')))
        common.wait_element(self.browser, '//th[contains(.,"Payor")]/a/i')

        if self.browser.does_page_contain_element('//li/a[@data-click="openMenu"]'):
            if self.browser.find_element('//li/a[@data-click="openMenu"]').is_displayed():
                common.log_message('data-click="openMenu"')
                common.click_and_wait(self.browser, '//li/a[@data-click="openMenu"]', "//li/a[text()='Filters']")

        # Apply filter
        common.wait_element(self.browser, "//li/a[text()='Filters']")
        self.browser.click_element_when_visible("//li/a[text()='Filters']")

        common.wait_element(self.browser, "//a/span[text()='Saved filters']")
        if self.browser.does_page_contain_element("//a/span[text()='" + filter_name + "']"):
            if not self.browser.find_element("//a/span[text()='" + filter_name + "']").is_displayed():
                self.browser.click_element_when_visible("//a/span[text()='Saved filters']")
        else:
            self.browser.click_element_when_visible("//a/span[text()='Saved filters']")
        common.wait_element(self.browser, "//a/span[text()='" + filter_name + "']")
        self.browser.click_element_when_visible("//a/span[text()='" + filter_name + "']")
        common.wait_element(self.browser, "//li[contains(@class, 'filter-highlight')]")

        # Update filters value
        updated_url = self.browser.get_location()
        if sort_by_client:
            updated_url = re.sub(r'sort=\w+', 'sort=client', updated_url)
        updated_url += additional_params

        self.browser.go_to(updated_url)

        self.browser.wait_until_element_is_not_visible("//em[text()='Agreed charges: <loading>']", datetime.timedelta(seconds=60))
        date_range = '{} - {}'.format(self.start_date.strftime('%b %d'), self.end_date.strftime('%b %d'))
        if not self.browser.does_page_contain_element('//span[text()="' + date_range + '"]'):
            self.browser.go_to(updated_url)
            self.browser.wait_until_element_is_not_visible("//em[text()='Agreed charges: <loading>']", datetime.timedelta(seconds=60))

    def find_header_index(self, required_headers: list, header_selector: str = '//thead/tr[@class="white"]', plus_int: int = 0) -> dict:
        headers_index: dict = {}
        find_headers: list = self.browser.find_elements(header_selector)

        for row in find_headers:
            count: int = 0
            for header in required_headers:
                if header.lower() in row.text.lower():
                    count += 1
            if count == len(required_headers):
                headers_columns = row.find_elements_by_tag_name("th")
                for column_name in headers_columns:
                    tmp_column_name = column_name.text.lower()
                    if tmp_column_name in required_headers and tmp_column_name not in headers_index:
                        headers_index[tmp_column_name] = headers_columns.index(column_name) + plus_int
                    if tmp_column_name == 'agreed' and tmp_column_name in headers_index:
                        headers_index['charges_agreed'] = headers_columns.index(column_name) + plus_int
                break

        return headers_index

    def open_second_tab(self) -> None:
        # Open new tab for processing
        self.browser.execute_javascript("window.open('" + self.url + "');")
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])
        self.browser.set_window_size(1920, 1080)
        self.browser.maximize_browser_window()
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[0])

    def is_no_results(self, message: str) -> bool:
        common.wait_element(self.browser,
                            '//div[text()="No results matched your keywords, filters, or date range" and not(@style="display: none;")]',
                            timeout=3,
                            is_need_screen=False
                            )
        if self.browser.does_page_contain_element('//div[text()="No results matched your keywords, filters, or date range" and not(@style="display: none;")]'):
            common.log_message(message, 'ERROR')
            return True
        return False

    def open_window_with_clients(self) -> None:
        common.click_and_wait(
            browser=self.browser,
            locator_for_click="//th/div/a/span[contains(.,'Client')]/../../../a/i",
            locator_for_wait="//div/span[text()='clients']"
        )
        self.browser.wait_until_element_is_not_visible('//div/span[text()="clients"]/../../div/div[@data-bind="visible: loading()"]')
        common.wait_element(self.browser, "//div/span[text()='clients']/../../div/ul/li")

    def get_list_of_clients_from_current_page(self) -> list:
        try_count: int = -1
        valid_clients: list = []

        while len(valid_clients) == 0 and try_count <= 3:
            if len(valid_clients) == 0:
                time.sleep(1)
            all_clients = self.browser.find_elements('//div/span[text()="clients"]/../../div/ul/li')

            for client in all_clients:
                if len(client.text) == 0:
                    continue
                valid_clients.append(str(client.text))
            try_count += 1

        return valid_clients

    def is_click_next_clients_page(self) -> bool:
        selector_next_element = '//div/span[text()="clients"]/../../div/ul/li/a[@data-bind="visible: canPageUp"]'

        if self.browser.does_page_contain_element(selector_next_element):
            if self.browser.find_element(selector_next_element).is_displayed():
                self.browser.click_element_when_visible(selector_next_element)
                self.browser.wait_until_element_is_not_visible('//div/span[text()="clients"]/../../div/div[@data-bind="visible: loading()"]')
                return True
            else:
                return False
        else:
            return False

    def get_list_of_clients(self) -> list:
        self.open_window_with_clients()

        full_list_of_valid_clients: list = self.get_list_of_clients_from_current_page()

        while True:
            if self.is_click_next_clients_page():
                temp: list = self.get_list_of_clients_from_current_page()
                full_list_of_valid_clients += temp
            else:
                break

        return full_list_of_valid_clients

    def scroll_into_view_client(self, selector_client_name: str, selector_client_selected: str) -> None:
        try:
            while not self.browser.does_page_contain_element(selector_client_name):
                if not self.is_click_next_clients_page():
                    return
            common.wait_element(self.browser, selector_client_name)
            self.browser.scroll_element_into_view(selector_client_name)
        except:
            pass
        finally:
            self.browser.click_element_when_visible(selector_client_name)
            common.wait_element(self.browser, selector_client_selected)

    def select_client_from_list(self, client_name: str) -> str:
        if "'" in client_name:
            selector_client_name = '//a[contains(., "' + client_name + '") or contains(., "' + client_name.replace(' ', '  ') + '")]'
            selector_client_selected = '//em[contains(., "Client: ' + client_name + '") or contains(., "' + client_name.replace(' ', '  ') + '")]'
            self.scroll_into_view_client(selector_client_name, selector_client_selected)
        else:
            selector_client_name = "//a[contains(., '" + client_name + "') or contains(., '" + client_name.replace(' ', '  ') + "')]"
            selector_client_selected = "//em[contains(., 'Client: " + client_name + "') or contains(., '" + client_name.replace(' ', '  ') + "')]"
            self.scroll_into_view_client(selector_client_name, selector_client_selected)
        tmp_elem = self.browser.find_element('//a[contains(@class, "filter-clientid")]/../a[@contactid]')
        client_id = tmp_elem.get_attribute('contactid')

        return client_id

    def apply_label(self, label_add: str, label_remove: str = '') -> None:
        common.wait_element(self.browser, '//button[contains(., "Label selected")]')
        self.browser.click_element_when_visible('//button[contains(., "Label selected")]')

        if label_add:
            common.wait_element(self.browser, '//h4[text()="Apply Labels"]/../../div/div/ul/li/input')
            self.browser.input_text('//h4[text()="Apply Labels"]/../../div/div/ul/li/input', label_add)
            common.wait_element(self.browser, '//div[text()="' + label_add + '" and @role="option"]')
            if self.browser.does_page_contain_element(
                    "//div[@id='select2-drop']/ul[@class='select2-results']/li[@class='select2-no-results']"):
                self.browser.input_text('//h4[text()="Apply Labels"]/../../div/div/ul/li/input', label_add.lower())
                common.wait_element(self.browser, '//div[text()="' + label_add + '" and @role="option"]')
            self.browser.click_element_when_visible('//div[text()="' + label_add + '" and @role="option"]')
        if label_remove:
            common.wait_element(self.browser, '//h4[text()="Remove Labels"]/../../div/div/ul/li/input')
            self.browser.input_text('//h4[text()="Remove Labels"]/../../div/div/ul/li/input', label_remove)
            common.wait_element(self.browser, '//div[text()="' + label_remove + '" and @role="option"]')
            if self.browser.does_page_contain_element(
                    "//div[@id='select2-drop']/ul[@class='select2-results']/li[@class='select2-no-results']"):
                self.browser.input_text('//h4[text()="Remove Labels"]/../../div/div/ul/li/input', label_remove.lower())
                common.wait_element(self.browser, '//div[text()="' + label_remove + '" and @role="option"]')
            self.browser.click_element_when_visible('//div[text()="' + label_remove + '" and @role="option"]')

        self.browser.click_element_when_visible('//button[text()="Apply Label Changes"]')
        self.browser.wait_until_element_is_not_visible('//button[text()="Apply Label Changes"]')
        self.browser.wait_until_element_is_not_visible('//h2[text()="Bulk Apply Labels"]')

    def get_agreed_rates(self, timesheet: Timesheet) -> float:
        rate: float or None = timesheet.get_rate()
        if rate is not None:
            return rate

        table_of_rates = self.mapping.fee_schedule_rates.copy()

        # filtering by provider
        if timesheet.current_payor.lower() in self.mapping.payor_mapping:
            fee_sched = self.mapping.payor_mapping[timesheet.current_payor.lower()]
        else:
            common.log_message('Payor {} not found in the mapping file'.format(timesheet.current_payor), 'ERROR')
            return .0
        # filtering by insurance short name
        table_of_rates.filter_by_column(table_of_rates.columns.index('FeeSched'), lambda x: str(x).strip().lower() == fee_sched.strip().lower())
        if len(table_of_rates) == 0:
            common.log_message('FeeSched name {} not found on "Fee Schedule Rates" sheet'.format(fee_sched), 'ERROR')
            return .0

        # filtering by cd number
        temp_table_of_rates = table_of_rates.copy()
        table_of_rates.filter_by_column(table_of_rates.columns.index('CdNum'), lambda x: str(x).replace('.0', '').strip().upper() == timesheet.service_code)
        if len(table_of_rates) == 0:
            common.log_message('CdNum {} not found on "Fee Schedule Rates" sheet'.format(timesheet.service_code))
            if timesheet.service_code.upper() in self.crosswalk_guide and len(self.crosswalk_guide[timesheet.service_code.upper()]) == 1:
                service_code_new: str = self.crosswalk_guide[timesheet.service_code.upper()][0]['code']
                common.log_message(f'Try new service code { service_code_new }')
                temp_table_of_rates.filter_by_column(temp_table_of_rates.columns.index('CdNum'), lambda x: str(x).replace('.0', '').strip().upper() == service_code_new.upper())
                if len(temp_table_of_rates) == 0:
                    common.log_message('CdNum {} not found on "Fee Schedule Rates" sheet'.format(service_code_new))
                    return .0
                table_of_rates = temp_table_of_rates
            else:
                return .0

        # filtering by cd dscrpt
        temp_table_of_rates = table_of_rates.copy()
        table_of_rates.filter_by_column(table_of_rates.columns.index('CdDscrpt'), lambda x: timesheet.service_dscrpt.upper() in str(x).strip().upper())
        if len(table_of_rates) == 0:
            table_of_rates = temp_table_of_rates

        def is_other_column_valid(current_row) -> bool:
            if 'Tricare' in current_row['FeeSched'] and current_row['Location'] is None:
                return False
            if current_row['Certificate'] is None and current_row['Education'] is None and current_row['Location'] is None:
                return True

            is_location_valid: bool = True
            if current_row['Location'] is not None:
                is_location_valid = False
                if type(current_row['Location']) == str:
                    for location_name in str(current_row['Location']).replace('&', ',').split(','):
                        location_name = location_name.strip()
                        if f'{location_name}"' in timesheet.provider.tags:
                            is_location_valid = True
                        elif location_name in common.state_abbreviations:
                            if f'" {common.state_abbreviations[location_name]} Staff' in timesheet.provider.tags:
                                is_location_valid = True
                        elif f'" {location_name} Staff' in timesheet.provider.tags:
                            is_location_valid = True

                        if location_name in timesheet.provider.full_location_info:
                            is_location_valid = True

                        if is_location_valid:
                            break
                else:
                    is_location_valid = str(current_row['Location']).strip('.0') in timesheet.location

            is_education_valid: bool = True
            if current_row['Education'] is not None:
                is_education_valid = current_row['Education'] in timesheet.provider.tags
                if not is_education_valid and current_row['Education'] == 'PHD':
                    is_education_valid = 'PhD' in timesheet.provider.tags

            is_certificate_valid: bool = True
            if current_row['Certificate'] is not None:
                is_certificate_valid = current_row['Certificate'] in timesheet.provider.tags
                if not is_certificate_valid:
                    if current_row['Certificate'] == 'BCBA':
                        is_certificate_valid = 'Masters' in timesheet.provider.tags or 'PhD' in timesheet.provider.tags
                    elif current_row['Certificate'] == 'BCaBA':
                        is_certificate_valid = 'Masters' in timesheet.provider.tags or 'Bachelors' in timesheet.provider.tags
                if not is_certificate_valid and str(current_row['Certificate']).strip().upper() == 'RBT':
                    if 'Tricare' not in current_row['FeeSched'] and 'Humana' not in current_row['FeeSched']:
                        is_certificate_valid = True
            return is_certificate_valid and is_education_valid and is_location_valid

        current_rate: float = 0.0
        modifiers: str = ''
        for row in table_of_rates:
            if row['Effective'] is not None and row['Effective'] <= timesheet.date_of_service and (row['Effective_2'] is None or row['Effective_2'] > timesheet.date_of_service):
                if is_other_column_valid(row) or len(table_of_rates) == 1:
                    if row['Rate'] > current_rate:
                        current_rate = row['Rate']
                        if row['Modifiers']:
                            modifiers = str(row['Modifiers'])
            elif row['Effective_2'] is not None and row['Effective_2'] < timesheet.date_of_service:
                if is_other_column_valid(row) or len(table_of_rates) == 1:
                    if row['Rate_2'] > current_rate:
                        current_rate = row['Rate_2']
                        if row['Modifiers']:
                            modifiers = str(row['Modifiers'])

        if current_rate > 0.0:
            timesheet.set_rate(current_rate)
            timesheet.modifiers = modifiers
        return current_rate

    def select_rows(self, timesheets: list) -> None:
        for timesheet in timesheets:
            self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{ timesheet.timesheet_id }"]/td/input')
            self.browser.select_checkbox(f'//tr[@id="billing-grid-row-{ timesheet.timesheet_id }"]/td/input')

    def unselect_rows(self, timesheets: list) -> None:
        for timesheet in timesheets:
            self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{ timesheet.timesheet_id }"]/td/input')
            self.browser.unselect_checkbox(f'//tr[@id="billing-grid-row-{ timesheet.timesheet_id }"]/td/input')

    def update_agreed_rate(self, agreed_rate: str, timesheet_id: str) -> bool:
        self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/div/button')
        self.browser.click_element_when_visible(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/div/button')

        common.wait_element(self.browser, f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td//a[text()=" Edit Timesheet"]')
        self.browser.click_element_when_visible(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td//a[text()=" Edit Timesheet"]')

        common.wait_element(self.browser, '//input[@id="rateClientAgreed"]', 60 * 3)

        self.browser.input_text_when_element_is_visible('//input[@id="rateClientAgreed"]', agreed_rate)
        common.wait_element(self.browser, '//button/span[text()="SUBMIT"]/..')
        time.sleep(3)
        self.browser.click_element_when_visible('//button/span[text()="SUBMIT"]/..')
        try:
            self.browser.wait_until_element_is_not_visible('//button/span[text()="SUBMIT"]/..', datetime.timedelta(seconds=10))
        except:
            try:
                self.browser.click_element_when_visible('//button/span[text()="SUBMIT"]/..')
                self.browser.wait_until_element_is_not_visible('//button/span[text()="SUBMIT"]/..', datetime.timedelta(seconds=10))
            except:
                self.browser.click_element_when_visible('//a[text()=" back"]')
                return False
        return True

    def get_payment_count(self, timesheet_id: str) -> str:
        self.browser.scroll_element_into_view(
            f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/a[@data-title="Click to view or add payments"]'
        )
        self.browser.driver.execute_script(
            "arguments[0].click();", self.browser.find_element(
                f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/a[@data-title="Click to view or add payments"]'
            )
        )

        common.wait_element(self.browser, '(//span[text()=" Payments"])[last()]/span', is_need_screen=False)
        time.sleep(1)
        payment_count: str = self.browser.get_text('(//span[text()=" Payments"])[last()]/span')
        if not payment_count:
            payment_count = '0'

        self.browser.driver.execute_script(
            "arguments[0].click();", self.browser.find_element(
                f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/a[@data-title="Click to view or add payments"]'
            )
        )
        self.browser.wait_until_element_is_not_visible('(//span[text()=" Payments"])[last()]/span')
        return payment_count

    def select_rows_and_apply_label(self, timesheets: list, label_add: str, label_remove: str = '') -> None:
        if not label_remove:
            timesheets_id: list = [timesheet.timesheet_id for timesheet in timesheets]
            common.log_message(f'ERROR: Label "{label_add}" applied to timesheet { ", ".join(timesheets_id) }')
            for timesheet in timesheets:
                timesheet.is_valid = False

        self.select_rows(timesheets)
        self.apply_label(label_add, label_remove)
        self.unselect_rows(timesheets)

    @staticmethod
    def get_insurance_name_and_date(text_from_web: str, type_of_insurance: str = 'Secondary'):
        valid_from = re.search(r'valid from: (\d{2}/\d{2}/\d{4})( to (\d{2}/\d{2}/\d{4})|)', text_from_web.lower())
        start_date: datetime = datetime.datetime.strptime(valid_from[1], '%m/%d/%Y')
        if valid_from[3] is None:
            end_date: datetime = datetime.datetime.now()
        else:
            end_date: datetime = datetime.datetime.strptime(valid_from[3], '%m/%d/%Y')
        insurance_name: str = re.search(f'{ type_of_insurance }: (.+)\n', text_from_web)[1].strip()

        return insurance_name, start_date, end_date

    def verify_insurance_info(self, client: Client) -> None:
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])
        self.browser.go_to(f'https://members.centralreach.com/#contacts/details/?id={ client.client_id }&mode=profile&edit=payors')
        common.wait_element(self.browser, '//a[@href="#insurance"]')
        common.wait_element(self.browser, '//div[@class="row"]')

        for row in self.browser.find_elements('//div[@class="row"]'):
            try:
                text_from_web: str = row.text.strip()
                if text_from_web and 'primary' in text_from_web.lower():
                    insurance_name, start_date, end_date = self.get_insurance_name_and_date(text_from_web, 'Primary')

                    if insurance_name in self.list_of_non_insurance:
                        continue

                    client.insurances.append(
                        Insurance(insurance_name, start_date, end_date, True)
                    )
                elif text_from_web and 'secondary' in text_from_web.lower():
                    insurance_name, start_date, end_date = self.get_insurance_name_and_date(text_from_web, 'Secondary')

                    if insurance_name in self.list_of_non_insurance:
                        continue

                    client.insurances.append(
                        Insurance(insurance_name, start_date, end_date, False)
                    )
            except Exception as ex:
                print('verify_insurance_info(): ' + str(ex))

        self.browser.go_to(self.base_url)
        self.browser.switch_window(browser_tabs[0])

    def get_insurance_details(self, client: Client):
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])
        self.browser.go_to(f'https://members.centralreach.com/#contacts/details/?id={ client.client_id }&mode=profile&edit=payors')
        common.wait_element(self.browser, '//a[@href="#insurance"]')
        common.wait_element(self.browser, '//a[text()="Details"]')

        for i in range(len(self.browser.find_elements('//a[text()="Details"]'))):
            try:
                index: int = i + 1
                time.sleep(1)
                self.browser.scroll_element_into_view(f'(//a[text()="Details"])[{ index }]')
                self.browser.click_element_when_visible(f'(//a[text()="Details"])[{ index }]')

                common.wait_element(self.browser, '//div[@data-bind="text: insuranceAddress"]')
                insurance_name: str = self.browser.get_text('//b[@data-bind="text: insuranceCompany"]')

                if insurance_name in self.list_of_non_insurance:
                    self.browser.click_element_when_visible('//input[@value="Cancel"]')
                    common.wait_element(self.browser, '//a[@href="#insurance"]')
                    continue

                insurance_type: str = self.browser.get_value('//select[contains(@data-bind, "payerResponsibility")]')
                date_from: str = self.browser.get_value('//input[contains(@data-bind, "coverageFrom")]')
                date_to: str = self.browser.get_value('//input[contains(@data-bind, "coverageTo")]')
                temp_insurance: Insurance = client.get_insurance(insurance_name, insurance_type, date_from, date_to)

                temp_insurance.address = self.browser.get_text('//div[@data-bind="text: insuranceAddress"]')
                temp_id: str = self.browser.get_text('//div[@data-bind="text: insurancePayerIds"]')
                if re.findall(r'ID: (.+)\)', temp_id):
                    temp_id = re.findall(r'ID: (.+)\)', temp_id)[0]
                if temp_id.strip().lower() == 'n/a':
                    temp_id = ''
                temp_insurance.payer_id = str(temp_id).strip()

                self.browser.click_element_when_visible('//span[text()="Subscriber"]')
                common.wait_element(self.browser, '//div[@id="patient-subscriber"]//input[@placeholder="First Name"]')
                temp_insurance.subscriber_first_name = str(self.browser.get_value('//div[@id="patient-subscriber"]//input[@placeholder="First Name"]')).strip()
                temp_insurance.subscriber_last_name = str(self.browser.get_value('//div[@id="patient-subscriber"]//input[@placeholder="Last Name"]')).strip()
                temp_insurance.subscriber_middle_name = str(self.browser.get_value('//div[@id="patient-subscriber"]//input[@placeholder="Middle"]')).strip()
                temp_insurance.subscriber_gender = str(self.browser.get_value('//div[@id="patient-subscriber"]//select[contains(@data-bind, "gender")]')).strip()
                temp_insurance.subscriber_address = str(self.browser.get_value('//div[@id="patient-subscriber"]//input[@placeholder="Address"]')).strip()
                temp_insurance.subscriber_id = str(self.browser.get_value('//div[@id="patient-subscriber"]//input[@placeholder="Insured ID"]')).strip()

                month: str = str(self.browser.get_value('//div[@id="patient-subscriber"]//input[@placeholder="Month"]')).strip()
                day: str = str(self.browser.get_value('//div[@id="patient-subscriber"]//input[@placeholder="Day"]')).strip()
                year: str = str(self.browser.get_value('//div[@id="patient-subscriber"]//input[@placeholder="Year"]')).strip()
                temp_insurance.subscriber_dob = ''
                if month and day and year:
                    temp_insurance.subscriber_dob = f'{month}/{day}/{year}'

                self.browser.click_element_when_visible('//input[@value="Cancel"]')
                common.wait_element(self.browser, '//a[@href="#insurance"]')

            except Exception as ex:
                print('get_insurance_details(): ' + str(ex))
        self.browser.go_to(self.base_url)
        self.browser.switch_window(browser_tabs[0])

    def is_flip_primary_to_secondary(self, timesheet: Timesheet) -> bool:
        try:
            if not timesheet.client.insurances:
                self.verify_insurance_info(timesheet.client)

            timesheet.set_insurances()

            if not timesheet.secondary_payor:
                return False
            if timesheet.current_payor.lower().startswith('s: '):
                return True
            timesheet.set_position_of_secondary_insurance(timesheet.secondary_payor)

            self.browser.click_element_when_visible(f'//tr[@id="billing-grid-row-{ timesheet.timesheet_id }"]/td/div[@data-title="Click to change payor"]/span')
            common.wait_element(self.browser, '//h3[text()="Edit payor"]')

            try:
                self.browser.click_element_when_visible(f'(//option[contains(., "Secondary: {timesheet.secondary_payor.payer_name}")])[{timesheet.position_of_secondary_payor}]')
            except:
                elems: list = self.browser.find_elements(f'//option[contains(., "Secondary: { timesheet.secondary_payor.payer_name }")]')
                count: int = 0
                for elem in elems:
                    if timesheet.secondary_payor.payer_name in elem.text:
                        count += 1
                        if count == timesheet.position_of_secondary_payor:
                            elem.click()
                            break

            self.browser.click_element_when_visible('//button[@type="submit"]')
            self.browser.wait_until_element_is_not_visible('//h3[text()="Edit payor"]')

            return True
        except Exception as error:
            common.log_message('is_flip_primary_to_secondary(): ' + str(error))
            return False

    @staticmethod
    def generate_dos_amount(timesheets_filters_free: list) -> dict:
        dos_amount: dict = {}

        for timesheet in timesheets_filters_free:
            if timesheet.service_code not in dos_amount:
                dos_amount[timesheet.service_code] = {
                    'billed': 0.0,
                    'paid_amount': 0.0
                }
            dos_amount[timesheet.service_code]['billed'] += timesheet.billed
            dos_amount[timesheet.service_code]['paid_amount'] += timesheet.amount_paid

        return dos_amount

    def does_amount_match(self, timesheets: list, timesheets_filters_free: list, eob: dict) -> bool:
        dos_amount: dict = self.generate_dos_amount(timesheets_filters_free)

        is_valid: bool = True
        for timesheet in timesheets:
            is_one_valid: bool = False

            if timesheet.service_code in eob['services']:
                for service in eob['services'][timesheet.service_code]:
                    service_billed: float = round(float(service['billed'].replace(',', '')), 2)
                    if service_billed == round(timesheet.billed, 2) or \
                            service_billed == round(dos_amount[timesheet.service_code]['billed'], 2):
                        service_paid_amount: float = round(float(service['paid_amount'].replace(',', '')), 2)
                        if service_paid_amount == round(timesheet.amount_paid, 2) or \
                                service_paid_amount == round(dos_amount[timesheet.service_code]['paid_amount'], 2):
                            is_one_valid = True
                            break
            if not is_one_valid:
                is_valid = False
                self.select_rows_and_apply_label([timesheet], 'Mismatched Payment')
        return is_valid

    def uncheck_all_credentials_fields(self):
        common.wait_element(self.browser, '//div[@class="ag-tool-panel"]', 5, False)
        if not self.browser.does_page_contain_element('//div[@class="ag-tool-panel"]'):
            self.browser.click_element('//button/i[contains(@class, "fa-columns")]/..')
            common.wait_element(self.browser, '//div[@class="ag-tool-panel"]', 30, False)

        while True:
            elems = self.browser.find_elements('//span[@class="ag-checkbox-checked"]')
            try:
                is_clicked = False
                for elem in elems:
                    if elem.is_displayed():
                        elem.click()
                        is_clicked = True
                        break
                if not is_clicked:
                    break
            except:
                pass

    def check_credentials_of_provider(self, provider: Provider, insurance_name: str, date_of_service: datetime) -> bool:
        short_insurance_name: str = insurance_name.split(':')[0].lower().strip()
        if short_insurance_name.lower().strip() in self.mapping.bcba_mapping:
            tmp_insurance_name = self.mapping.bcba_mapping[short_insurance_name.lower().strip()]
        else:
            return True
        list_of_insurances: list = []
        for insurance in tmp_insurance_name.split('&'):
            list_of_insurances.append(str(insurance).strip())

        if provider.credentials:
            list_of_valid: list = []
            for insurance in list_of_insurances:
                if insurance in provider.credentials:
                    for credential in provider.credentials[insurance]:
                        if credential['effective'] <= date_of_service <= credential['expires']:
                            list_of_valid.append(insurance)
                            break
            if len(list_of_valid) == len(list_of_insurances):
                return True

        try:
            browser_tabs = self.browser.get_window_handles()
            self.browser.switch_window(browser_tabs[2])
            self.browser.go_to(f'https://members.centralreach.com/#resources/templatesreport/?templateId=3997&contactId={ provider.provider_id}')

            common.wait_element_and_refresh(self.browser, '//em[contains(.,"Provider ID:") or contains(.,"Not Found")]')
            if self.browser.does_page_contain_element('//em[contains(.,"Not Found")]'):
                return False

            self.uncheck_all_credentials_fields()

            list_of_valid: list = []
            credentials: list = []
            for insurance in list_of_insurances:
                all_items = self.browser.find_elements('//span[@class="ag-column-select-label"]')
                for item in all_items:
                    if insurance.lower() == item.text.lower():
                        item.click()
                        break
                common.wait_element(self.browser, f'//span[contains(., "{ insurance }") and @ref="eText"]', 15, False)
                effective: list = self.browser.find_elements('//li//div/div[contains(., "Effective")]')
                expires: list = self.browser.find_elements('//li//div/div[contains(., "Expires")]')
                for e_date in effective[len(credentials):]:
                    try:
                        effective_date: datetime = datetime.datetime.strptime(str(e_date.get_attribute('innerText')).split(':')[-1].strip(), '%m/%d/%y')
                        expires_temp: str = str(expires[effective.index(e_date)].get_attribute('innerText')).split(':')[-1].strip().lower()
                        if expires_temp == 'n/a':
                            expires_date: datetime = datetime.datetime.now()
                        else:
                            expires_date: datetime = datetime.datetime.strptime(expires_temp, '%m/%d/%y')

                        if insurance not in provider.credentials:
                            provider.credentials[insurance] = []
                        provider.credentials[insurance].append({'effective': effective_date, 'expires': expires_date})
                        if insurance not in list_of_valid and effective_date <= date_of_service <= expires_date:
                            list_of_valid.append(insurance)

                        credentials.append({'name': insurance, 'effective': effective_date, 'expires': expires_date})
                    except Exception as error:
                        common.log_message('check_domo_provider_id(): ' + str(error))

            if len(list_of_valid) == len(list_of_insurances):
                return True
        except Exception as ex:
            common.log_message('ERROR in check_domo_provider_id(): ' + str(ex), 'ERROR')
        finally:
            self.browser.go_to(self.base_url)
            browser_tabs = self.browser.get_window_handles()
            self.browser.switch_window(browser_tabs[0])
        return False

    def generate_secondary_claim(self, timesheets: list) -> str:
        timesheet_id: str = timesheets[0].timesheet_id

        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])
        self.browser.go_to(f'https://members.centralreach.com/#claims/list/?billingEntryId={timesheets[0].timesheet_id}')
        common.wait_element(self.browser, f'//em[text()="Billing Entry: Entry ID: {timesheet_id}"]')

        self.browser.click_element_when_visible('//tr[contains(@id, "billing-grid-row-")]/td/div/a[@id="actionsDD"]')
        common.wait_element(self.browser, '//tr[contains(@id, "billing-grid-row-")]/td//a[contains(., "Generate Secondary Claim")]')
        self.browser.click_element_when_visible('//tr[contains(@id, "billing-grid-row-")]/td//a[contains(., "Generate Secondary Claim")]')
        common.wait_element(self.browser, '//tbody[@data-bind="foreach: payers"]/tr')
        header: dict = self.find_header_index(['policy id'], '//thead/tr', 1)

        policy_id: str = self.browser.get_text(f'//tbody[@data-bind="foreach: payers"]/tr/td[{ header["policy id"] }]')

        self.browser.click_element_when_visible('//button[text()="Generate"]')
        common.wait_element(self.browser, '//button[contains(., "Save & Move to Inbox")]', is_need_screen=False)
        if self.browser.does_page_contain_element('//div[text()="There was an error when trying to generate a secondary claim:"]/../div[contains(@class, "alert-danger")]'):
            error: str = self.browser.get_text('//div[text()="There was an error when trying to generate a secondary claim:"]/../div[contains(@class, "alert-danger")]')
            common.log_message(error)
            self.browser.reload_page()
            policy_id = ''
        self.browser.switch_window(browser_tabs[0])
        return policy_id

    def populate_provider_tab(self, timesheets: list, policy_id: str) -> bool:
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])
        common.wait_element(self.browser, '//span[text()="Patient"]')
        self.browser.click_element_when_visible('//span[text()="Patient"]')

        common.wait_element(self.browser, '//a[contains(.,"Patient")]')
        self.browser.click_element_when_visible('//a[contains(.,"Patient")]')

        common.wait_element(self.browser, '//input[@id="patient-patient-providerid"]')
        self.browser.input_text_when_element_is_visible('//input[@id="patient-patient-providerid"]', policy_id)

        common.wait_element(self.browser, '//span[text()="Providers"]')
        self.browser.click_element_when_visible('//span[text()="Providers"]')

        common.wait_element(self.browser, '//a[contains(.,"Provider/Supplier")]')
        self.browser.click_element_when_visible('//a[contains(.,"Provider/Supplier")]')

        provider_id: str = ''
        try:
            common.wait_element(self.browser, '//abbr[@data-column="RendProvLast"]/../..//a')
            provider_from_web: str = self.browser.get_text('//abbr[@data-column="RendProvLast"]/../..//a')
            provider_id = re.search(r'ID: (\d+)', provider_from_web)[1]
        except Exception as ex:
            common.log_message('generate_secondary_claim(): ' + str(ex))

        timesheets[0].claim_id = self.browser.get_text('//span[@data-bind="text: currentClaim().id()"]')
        common.log_message(f'Claim {timesheets[0].claim_id} generated')

        self.browser.switch_window(browser_tabs[0])

        provider: Provider = self.get_provider('', provider_id)
        return self.check_credentials_of_provider(provider, timesheets[0].current_payor, timesheets[0].date_of_service)

    # TODO redo
    def does_service_code_match(self, table: Table, service_code: str) -> dict or bool:
        temp_table: Table = table.copy()
        temp_table.filter_by_column(self.mapping.fee_schedule_columns_index['CdNum'], lambda x: str(x).replace('.0', '').strip().upper() == service_code.upper())
        if len(temp_table) == 0:
            result: dict = {}
            for item in self.crosswalk_guide[service_code]:
                temp_table: Table = table.copy()
                temp_table.filter_by_column(self.mapping.fee_schedule_columns_index['CdNum'], lambda x: str(x).replace('.0', '').strip().upper() == item['code'].upper())
                if len(temp_table) > 0:
                    result['code'] = item['code']
                    result['conversion'] = item['conversion']
                    result['modifiers'] = table[0][self.mapping.fee_schedule_columns_index['Code Modifiers']]
                    result['bachelors degree'] = table[0][self.mapping.fee_schedule_columns_index['Bachelors Degree']]
                    result['less than bachelors'] = table[0][self.mapping.fee_schedule_columns_index['Less than Bachelors']]
                    result['doctorate'] = table[0][self.mapping.fee_schedule_columns_index['Doctorate']]
                    return result
            return False
        return True

    def validate_service_code(self, timesheets: list, fee_sched: str) -> (int, int):
        table = self.mapping.fee_schedule_table.copy()
        table.filter_by_column(self.mapping.fee_schedule_columns_index['FeeSched'], lambda x: str(x).strip().lower() == fee_sched.lower())
        valid_timesheets: int = 0
        not_valid_timesheets: int = 0

        for timesheet in timesheets:
            if fee_sched in self.crosswalk_guide_populated and timesheet.service_code in self.crosswalk_guide_populated[fee_sched]:
                if type(self.crosswalk_guide_populated[fee_sched][timesheet.service_code]) == bool:
                    if self.crosswalk_guide_populated[fee_sched][timesheet.service_code]:
                        valid_timesheets += 1
                    else:
                        not_valid_timesheets += 1
            else:
                if fee_sched not in self.crosswalk_guide_populated:
                    self.crosswalk_guide_populated[fee_sched] = {}
                self.crosswalk_guide_populated[fee_sched][timesheet.service_code] = self.does_service_code_match(table, timesheet.service_code)
                if type(self.crosswalk_guide_populated[fee_sched][timesheet.service_code]) == bool:
                    if self.crosswalk_guide_populated[fee_sched][timesheet.service_code]:
                        valid_timesheets += 1
                    else:
                        not_valid_timesheets += 1
                        common.log_message(f'Unable to determine new service code for { fee_sched }. Current service code: { timesheet.service_code }')
        return valid_timesheets, not_valid_timesheets

    @staticmethod
    def get_modifiers(modifiers: dict, provider: Provider) -> list:
        list_of_modifiers: list = []

        if modifiers['modifiers']:
            list_of_modifiers.append(modifiers['modifiers'])

        if modifiers['bachelors degree'] and 'Bachelors' in provider.tags:
            list_of_modifiers.append(modifiers['bachelors degree'])
        if modifiers['less than bachelors'] and 'High School Diploma' in provider.tags:
            list_of_modifiers.append(modifiers['less than bachelors'])
        if modifiers['doctorate'] and ('Masters' in provider.tags or 'PhD' in provider.tags or 'Medical Doctorate' in provider.tags):
            list_of_modifiers.append(modifiers['doctorate'])

        return list_of_modifiers

    @staticmethod
    def does_modifier_exists(timesheets: list) -> bool:
        for timesheet in timesheets:
            if timesheet.modifiers:
                return True
        return False

    def update_service_code_info(self, timesheets: list, fee_sched: str, is_valid: bool) -> bool:
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])

        try:
            common.wait_element(self.browser, '//span[text()="Services"]')
            self.browser.click_element_when_visible('//span[text()="Services"]')

            common.wait_element(self.browser, '//tr[contains(@data-bind, "editServiceLine")]')
            headers: dict = self.find_header_index(['billing entry', 'service date'], '//table[contains(@class, "table-pointers")]')

            for timesheet in timesheets:
                if type(self.crosswalk_guide_populated[fee_sched][timesheet.service_code]) == bool and not timesheet.modifiers:
                    continue
                rows: list = self.browser.find_elements('//tr[contains(@data-bind, "editServiceLine")]')
                for row in rows:
                    columns: list = row.find_elements_by_tag_name('td')
                    timesheet_id_claim: str = columns[headers['billing entry']].text
                    date_claim: str = columns[headers['service date']].text
                    datetime_claim: datetime = datetime.datetime.strptime(date_claim, '%m/%d/%Y')
                    if (timesheet_id_claim == timesheet.timesheet_id or timesheet_id_claim == 'Combined') and datetime_claim == timesheet.date_of_service:
                        columns[headers['billing entry']].click()
                        time.sleep(5)
                        common.wait_element(self.browser, f'//tr[contains(@data-bind, "editServiceLine") and contains(@class, "active")]')
                        common.wait_element(self.browser, '//input[@id="service-details-code"]')
                        service_code_claim: str = self.browser.get_value('//input[@id="service-details-code"]')

                        if service_code_claim != timesheet.service_code:
                            continue

                        if not is_valid:
                            units_claim: int = int(self.browser.get_value('//input[@id="service-details-daysunits"]'))
                            self.browser.input_text_when_element_is_visible('//input[@id="service-details-code"]', self.crosswalk_guide_populated[fee_sched][timesheet.service_code]['code'])
                            self.browser.input_text_when_element_is_visible('//input[@id="service-details-daysunits"]', str(round(units_claim * self.crosswalk_guide_populated[fee_sched][timesheet.service_code]['conversion'])))

                        for i in range(1, 5):
                            modifier = self.browser.find_element(f'//input[@data-bind="value: modifier{i}"]')
                            modifier.send_keys('\ue003\ue003\ue003\ue003\ue003')

                        modifiers: list = []
                        if type(self.crosswalk_guide_populated[fee_sched][timesheet.service_code]) == bool:
                            if timesheet.modifiers:
                                modifiers: list = timesheet.modifiers.split(',')
                        else:
                            modifiers: list = self.get_modifiers(self.crosswalk_guide_populated[fee_sched][timesheet.service_code], timesheet.provider)
                        for modifier in modifiers:
                            self.browser.find_element(f'//input[@data-bind="value: modifier{ (modifiers.index(modifier) + 1) }"]').send_keys(modifier)
            return True
        except Exception as ex:
            common.log_message('check_service_code(): ' + str(ex), 'ERROR')
        finally:
            self.browser.switch_window(browser_tabs[0])
        return False

    def check_service_code(self, timesheets: list) -> bool:
        fee_sched: str = str(self.mapping.payor_mapping[timesheets[0].current_payor.lower()]).strip()
        valid_timesheets, not_valid_timesheets = self.validate_service_code(timesheets, fee_sched)
        if not_valid_timesheets > 0:
            return False
        elif valid_timesheets == len(timesheets) and not self.does_modifier_exists(timesheets):
            return True
        return self.update_service_code_info(timesheets, fee_sched, valid_timesheets == len(timesheets))

    def fix_claim_validation_errors(self):
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])

        try:
            common.wait_element(self.browser, '//span[text()="Patient"]')
            self.browser.click_element_when_visible('//span[text()="Patient"]')

            common.wait_element(self.browser, '//input[@id="patient-insurance-zip"]')
            zip_code: str = self.browser.get_value('//input[@id="patient-insurance-zip"]')
            if '--' in zip_code:
                zip_code = zip_code.replace('--', '-')
                self.browser.input_text_when_element_is_visible('//input[@id="patient-insurance-zip"]', zip_code)
        except Exception as error:
            common.log_message('fix_claim_validation_errors(): ' + str(error))

        self.browser.switch_window(browser_tabs[0])

    def save_and_move_to_inbox(self):
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])

        common.wait_element(self.browser, '//button[contains(., "Save & Move to Inbox")]')
        self.browser.click_element_when_visible('//button[contains(., "Save & Move to Inbox")]')
        common.wait_element(self.browser, '//button[contains(., "Saved")]')
        self.browser.switch_window(browser_tabs[0])

    def send_to_gateway(self, client_id: str, payor: str, claim_id: str) -> bool:
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])

        self.browser.go_to(f'https://members.centralreach.com/#claims/list/?clientId={ client_id }')
        common.wait_element(self.browser, f'//em[contains(., "(ID: { client_id }")]')

        self.browser.click_element_when_visible(f'//span[text()="{ claim_id }"]/../..//label')

        common.wait_element(self.browser, '//button[contains(., "Actions")]')
        self.browser.click_element_when_visible('//button[contains(., "Actions")]')

        common.wait_element(self.browser, '//a[text()="Send to Gateway"]')
        self.browser.click_element_when_visible('//a[text()="Send to Gateway"]')

        common.wait_element(self.browser, '//button[text()="Send to gateway"]')
        if 'CO Medicaid'.lower() in payor.lower():
            self.browser.select_checkbox('//input[@id="ignoreError2"]')

        is_success: bool = True
        try:
            self.browser.click_element_when_visible('//button[text()="Send to gateway"]')
            self.browser.wait_until_element_is_not_visible('//button[text()="Send to gateway"]', datetime.timedelta(seconds=60))
        except Exception as ex:
            common.log_message(str(ex))
            self.browser.capture_page_screenshot(os.path.join(
                os.environ.get("ROBOT_ROOT", os.getcwd()),
                'output',
                f'Something_went_wrong_Claim_{ claim_id }.png')
            )
            if self.browser.does_page_contain_element('//button[text()="Send to gateway"]'):
                if self.browser.find_element('//button[text()="Send to gateway"]').is_displayed():
                    is_success = False
                    self.browser.click_element_when_visible('//button[text()="Send to gateway"]/../..//button[@class="close"]')
            common.log_message(f'Button "Send to gateway" not available. Status: {is_success}')
        finally:
            self.browser.switch_window(browser_tabs[0])
        return is_success

    def get_timesheets_for_processing(self) -> dict:
        # Prepare dict of timesheets for processing
        rows: list = self.browser.find_elements('//tr[contains(@id, "billing-grid-row-")]')
        timesheets_by_date: dict = {}
        for row in rows:
            date: str = row.find_elements_by_tag_name('td')[self.headers_index['date']].text
            if date not in timesheets_by_date:
                timesheets_by_date[date] = []
            timesheets_by_date[date].append(Timesheet(row.get_attribute('id').split('-')[-1]))
        return timesheets_by_date

    def get_timesheets_data_filters_free(self, client_id) -> dict:
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[2])
        self.browser.go_to(
            'https://members.centralreach.com/#billingmanager/billing/?clientId={}&startdate={}&enddate={}&pageSize=2000'.format(
                client_id, self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d'))
        )
        common.wait_element(self.browser, '//em[contains(., "ID: ' + client_id + '")]')

        timesheets_filters_free: dict = {}
        rows: list = self.browser.find_elements('//tr[contains(@id, "billing-grid-row-")]')
        for row in rows:
            date: str = row.find_elements_by_tag_name('td')[self.headers_index['date']].text
            if date not in timesheets_filters_free:
                timesheets_filters_free[date] = []
            timesheet: Timesheet = Timesheet(row.get_attribute('id').split('-')[-1])

            columns: list = self.browser.find_elements(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td')
            timesheet.set_service(str(columns[self.headers_index['service/auth']].text).strip())
            timesheet.owed = float(str(self.browser.find_element(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td[{self.headers_index["owed"] + 1}]').text).replace(',', ''))
            timesheet.billed = float(self.browser.get_text(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td[contains(@class, "charge") and not(contains(@data-bind,"useAgreedView()"))]').replace(',', ''))
            timesheet.amount_paid = float(self.browser.get_text(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td/span[contains(@data-bind, "amountPaid")]').replace(',', ''))
            timesheets_filters_free[date].append(timesheet)

        self.browser.switch_window(browser_tabs[0])
        return timesheets_filters_free

    def get_client_location(self, client_id: str, insurance_name: str) -> str:
        location = ''
        self.browser.click_element_when_visible('//a[@contactid="' + client_id + '"]')
        common.wait_element(self.browser, '//small[text()="Upload File"]')
        common.wait_element(self.browser, '//a[text()=" Labels"]', timeout=10)
        if self.browser.does_page_contain_element('//a[text()=" Labels"]'):
            self.browser.click_element_when_visible('//a[text()=" Labels"]')
            time.sleep(0.5)

        common.wait_element(self.browser, '//span[@class="tag-name"]')
        labels = self.browser.find_elements('//span[@class="tag-name"]')
        for label in labels:
            if str(label.text).endswith('"'):
                location = str(label.text)[:-1]
                break

        if location and 'CO Medicaid'.lower() == insurance_name.lower():
            for key in self.trump_site_list:
                if location.strip().lower() in key.lower():
                    location = self.trump_site_list[key]
                    break
        elif not location:
            self.browser.reload_page()
            common.wait_element(self.browser, '//a[@data-title="Click to filter by this provider"]/../a[contains(@class, "vcard")]')
            self.browser.click_element_when_visible('//a[@data-title="Click to filter by this provider"]/../a[contains(@class, "vcard")]')
            common.wait_element(self.browser, '//a[text()=" Labels"]', timeout=10)
            if self.browser.does_page_contain_element('//a[text()=" Labels"]'):
                self.browser.click_element_when_visible('//a[text()=" Labels"]')
                time.sleep(0.5)

            common.wait_element(self.browser, '//span[@class="tag-name"]')
            labels = self.browser.find_elements('//span[@class="tag-name"]')
            for label in labels:
                if str(label.text).endswith('"'):
                    location = str(label.text)[:-1]
                    break

        return location

    def click_action_and_bulk_merge_claims(self) -> None:
        common.wait_element(self.browser, '//a[contains(., "Action")]')
        self.browser.click_element_when_visible('//a[contains(., "Action")]')

        common.wait_element(self.browser, '//a[contains(., "Bulk-merge Claims")]')
        self.browser.click_element_when_visible('//a[contains(., "Bulk-merge Claims")]')

    def bulk_merge_claims(self, insurance_name=''):
        self.click_action_and_bulk_merge_claims()
        common.wait_element(self.browser, '//button[contains(., "Start claims generation")]', 10, False)
        if self.browser.does_page_contain_element('//button[contains(., "Start claims generation")]'):
            if not self.browser.find_element('//button[contains(., "Start claims generation")]').is_displayed():
                self.click_action_and_bulk_merge_claims()
        else:
            self.click_action_and_bulk_merge_claims()
        common.wait_element(self.browser, '//button[contains(., "Start claims generation")]')

        if self.browser.does_page_contain_element('//span[text()="Collapse All"]'):
            if self.browser.find_element('//span[text()="Collapse All"]').is_displayed():
                self.browser.click_element_when_visible('//span[text()="Collapse All"]')
        common.wait_element(self.browser, '//th[contains(.,"Provider Supplier")]', timeout=15)

        if self.browser.does_page_contain_element('//span[text()="Collapse All"]'):
            if self.browser.find_element('//span[text()="Collapse All"]').is_displayed():
                self.browser.click_element_when_visible('//span[text()="Collapse All"]')
                print('retry click Collapse All')
        common.wait_element(self.browser, '//th[contains(.,"Provider Supplier")]', timeout=15)

        self.browser.unselect_checkbox('//input[contains(@data-bind, "includeTimes")]')
        self.browser.unselect_checkbox('//input[contains(@data-bind, "splitProviders")]')
        self.browser.unselect_checkbox('//input[contains(@data-bind, "useServiceLocation")]')

        if self.browser.does_page_contain_element('//input[contains(@data-bind, "splitAuth")]'):
            if self.browser.find_element('//input[contains(@data-bind, "splitAuth")]').is_displayed():
                if 'United Behavioral Health'.lower() == insurance_name.lower().strip():
                    self.browser.select_checkbox('//input[contains(@data-bind, "splitAuth")]')
                else:
                    self.browser.unselect_checkbox('//input[contains(@data-bind, "splitAuth")]')

    def sync_provider_supplier_fields(self) -> bool:
        all_providers_supplier = self.browser.find_elements('//a[contains(@data-bind, "providerSupplierName")]')
        index = -2
        any_empty_field = False
        is_different = False

        previous_provider = str(all_providers_supplier[0].text).lower()
        for provider_supplier in all_providers_supplier:
            provider_supplier_from_web = str(provider_supplier.text).lower()
            if previous_provider != provider_supplier_from_web:
                is_different = True
            if provider_supplier_from_web:
                if index == -2:
                    index = all_providers_supplier.index(provider_supplier)
            else:
                any_empty_field = True

        if any_empty_field and index != -2:
            sync_all = self.browser.find_elements('//a[contains(@data-bind, "syncField") and @data-syncfield="providerSupplier"]')
            sync_all[index].click()
        elif index == -2 or is_different:
            return False
        return True

    def sync_provider_to_provider_supplier(self):
        gears = self.browser.find_elements('//th[contains(.,"Provider")]/div/div/ul/li/a[text()="To provider supplier"]/../../../a/i')
        for index in range(1, len(gears) + 1):
            self.browser.click_element_when_visible(f'(//th[contains(.,"Provider")]/div/div/ul/li/a[text()="To provider supplier"]/../../../a/i)[{index}]')
            common.wait_element(self.browser, f'(//th[contains(.,"Provider")]//a[text()="To provider supplier"])[{index}]')
            self.browser.click_element_when_visible(f'(//th[contains(.,"Provider")]//a[text()="To provider supplier"])[{index}]')

    def sync_provider_supplier_to_provider(self):
        gears = self.browser.find_elements('//th[contains(.,"Provider Supplier")]/div/div/ul/li/a[text()="To provider"]/../../../a/i')
        for index in range(1, len(gears) + 1):
            self.browser.click_element_when_visible(f'(//th[contains(.,"Provider Supplier")]/div/div/ul/li/a[text()="To provider"]/../../../a/i)[{index}]')
            common.wait_element(self.browser, f'(//th[contains(.,"Provider Supplier")]//a[text()="To provider"])[{index}]')
            self.browser.click_element_when_visible(f'(//th[contains(.,"Provider Supplier")]//a[text()="To provider"])[{index}]')

    def check_provider_profile(self, providers_id: list) -> str:
        providers_id = sorted(providers_id, key=lambda i: i['hours'], reverse=True)
        provider_id = ''

        for provider in providers_id:
            try:
                browser_tabs = self.browser.get_window_handles()
                self.browser.switch_window(browser_tabs[1])
                self.browser.go_to('https://members.centralreach.com/#contacts/details/?id={}&mode=profile&edit=claims'.format(provider['clinician_id']))

                common.wait_element(self.browser, '//h2[text()="Custom Identifiers" or text()="Unable to load this contact"]')
                if self.browser.does_page_contain_element('//h2[text()="Unable to load this contact"]'):
                    continue
                else:
                    if self.browser.does_page_contain_element('//span[contains(., "Medicaid")]'):
                        provider_id = provider['clinician_id']
                        break
            except Exception as ex:
                common.log_message('check_provider_profile(): ' + str(ex), 'ERROR')
                provider_id = ''
            finally:
                self.browser.reload_page()
                browser_tabs = self.browser.get_window_handles()
                self.browser.switch_window(browser_tabs[0])

        common.log_message('Check profile CO Medicaid: provider id ' + provider_id, 'TRACE')
        return provider_id

    def check_domo_provider_id(self, providers_id: list, insurance_name: str) -> str:
        providers_id = sorted(providers_id, key=lambda i: i['hours'], reverse=True)
        provider_id = ''

        for provider in providers_id:
            try:
                browser_tabs = self.browser.get_window_handles()
                self.browser.switch_window(browser_tabs[1])
                self.browser.go_to(
                    'https://members.centralreach.com/#resources/templatesreport/?templateId=3997&contactId={}'.format(
                        provider['clinician_id'])
                )

                common.wait_element(self.browser, '//em[contains(.,"Provider ID:") or contains(.,"Not Found")]')
                if self.browser.does_page_contain_element('//em[contains(.,"Not Found")]'):
                    continue

                self.uncheck_all_credentials_fields()

                # Update insurance name
                if insurance_name.lower().strip() in self.mapping.bcba_mapping:
                    tmp_insurance_name = self.mapping.bcba_mapping[insurance_name.lower().strip()]
                else:
                    tmp_insurance_name = insurance_name.lower().strip()

                for insurance in tmp_insurance_name.split('&'):
                    all_items = self.browser.find_elements('//span[@class="ag-column-select-label"]')
                    for item in all_items:
                        if insurance.lower().strip() == item.text.lower():
                            item.click()
                            break

                if self.browser.does_page_contain_element('//div[@class="dropdown"]/div/a[contains(., "file")]'):
                    if len(self.browser.find_elements('//div[@class="dropdown"]/div/a[contains(., "file")]')) == \
                            len(tmp_insurance_name.split('&')):
                        provider_id = provider['clinician_id']
                        break
            except Exception as ex:
                common.log_message('ERROR in check_domo_provider_id(): ' + str(ex), 'ERROR')
                provider_id = ''
            finally:
                self.browser.reload_page()
                browser_tabs = self.browser.get_window_handles()
                self.browser.switch_window(browser_tabs[0])

        if not provider_id:
            if len(providers_id) == 2:
                provider_id = providers_id[0]['clinician_id']
            else:
                pass
                # update this logic in future
        return provider_id

    def find_domo_provider_id_and_change(self, client_id: str, insurance_name: str) -> bool:
        if client_id in self.domo_mapping_file or client_id in self.domo_mapping_site:
            previous_provider_id = ''
            for providers in (self.domo_mapping_file.get(client_id), self.domo_mapping_site.get(client_id)):
                if providers is None:
                    continue
                if len(providers) == 1:
                    provider_id = providers[0]['clinician_id']
                else:
                    if 'CO Medicaid'.lower() in insurance_name.lower():
                        provider_id = self.check_provider_profile(providers)
                    else:
                        provider_id = self.check_domo_provider_id(providers, insurance_name)
                if previous_provider_id and previous_provider_id == provider_id:
                    continue

                if provider_id:
                    previous_provider_id = provider_id
                    if self.validate_provider_by_id('Provider', provider_id):
                        if self.change_provider_by_id('Provider', provider_id):
                            return True
            common.log_message('ERROR: Provider cannot be determined for client ID {}'.format(client_id), 'ERROR')
        else:
            common.log_message('ERROR: Provider was not found in the mapping file or on the DOMO website for client ID {}'.format(client_id), 'ERROR')
        return False

    def validate_provider_by_id(self, column_name: str, provider_id: str) -> bool:
        browser_tabs = self.browser.get_window_handles()
        try:
            self.browser.switch_window(browser_tabs[0])
            url: str = self.browser.get_location()

            self.browser.switch_window(browser_tabs[1])
            self.browser.reload_page()
            self.browser.go_to(url)
            common.wait_element(self.browser, '//input[@data-bind="checked: listVm.allSelected"]')
            self.browser.select_checkbox('//input[@data-bind="checked: listVm.allSelected"]')
            self.bulk_merge_claims()

            if not self.search_provider_by_id(column_name, provider_id):
                self.browser.reload_page()
                self.browser.switch_window(browser_tabs[0])
                return False
            self.browser.go_to(self.base_url)
            self.browser.switch_window(browser_tabs[0])
            return True
        except Exception as ex:
            common.log_message('validate_provider_by_id(): ' + str(ex), 'ERROR')
            self.browser.capture_page_screenshot(
                os.path.join(os.environ.get(
                    "ROBOT_ROOT", os.getcwd()),
                    'output',
                    'Validate_provider_error_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
                )
            )
        finally:
            self.browser.switch_window(browser_tabs[0])

    def search_provider_by_id(self, column_name: str, provider_id: str) -> bool:
        self.browser.click_element_when_visible('//th[contains(.,"' + column_name + '")]/div/a[contains(@data-bind, "{title: \'Search for different provider\'}")]')

        common.wait_element(self.browser, '//th[contains(.,"' + column_name + '")]/div/div/input')
        self.browser.input_text_when_element_is_visible('//th[contains(.,"' + column_name + '")]/div/div/input', provider_id)

        common.wait_element(self.browser, '//li/div[contains(.,"' + provider_id + '")]', 10, False)
        if self.browser.does_page_contain_element('//li[text()="No matches found."]'):
            common.log_message('ERROR: Provider ID {} not found on Central Reach site'.format(provider_id))
            self.browser.execute_javascript('document.getElementById("select2-drop-mask").style.display = "None"')
            return False
        else:
            self.browser.click_element_when_visible('//li/div[contains(.,"' + provider_id + '")]')
        return True

    def check_and_update_billing(self, valid_billing: str, full_billing_name: str):
        all_billings = self.browser.find_elements('//a[contains(@data-bind, "billingName")]')
        for billing in all_billings:
            if valid_billing.lower() not in str(billing.text).lower():
                self.change_billing('Billing', full_billing_name)
                break

    def change_billing(self, column_name: str, billing: str):
        self.browser.click_element_when_visible('//th[contains(.,"' + column_name + '")]/div/a[contains(@data-bind, "{title: \'Search for different provider\'}")]')

        common.wait_element(self.browser, '//th[contains(.,"' + column_name + '")]/div/div/input')
        self.browser.input_text_when_element_is_visible('//th[contains(.,"' + column_name + '")]/div/div/input', billing)

        common.wait_element(self.browser, '//li/div[contains(.,"' + billing + '")]', timeout=10)
        if self.browser.does_page_contain_element('//li/div[contains(.,"' + billing + '")]'):
            self.browser.click_element_when_visible('//li/div[contains(.,"' + billing + '")]')

        self.sync_to_all_claims(column_name)

    def clear_location(self):
        self.click_button_by_text('Location', 'Clear location')
        self.sync_to_all_claims('Location')

    def clear_provider_supplier(self):
        self.click_button_by_text('Provider Supplier', 'Clear provider supplier')
        self.sync_to_all_claims('Provider Supplier')

    def clear_referrer(self):
        self.click_button_by_text('Referrer', 'Clear referrer')
        self.sync_to_all_claims('Referrer')

    def click_button_by_text(self, column_name: str, button_text: str):
        common.wait_element(self.browser, f'//th[contains(.,"{column_name}")]/div/div/a/i')
        self.browser.click_element_when_visible(f'//th[contains(.,"{column_name}")]/div/div/a/i')
        common.wait_element(self.browser, f'//th[contains(.,"{column_name}")]//a[text()="{button_text}"]')
        self.browser.click_element_when_visible(f'//th[contains(.,"{column_name}")]//a[text()="{button_text}"]')

    def sync_to_all_claims(self, column_name: str):
        common.wait_element(self.browser, f'//th[contains(.,"{column_name}")]/div/div/a/i')
        self.browser.click_element_when_visible(f'//th[contains(.,"{column_name}")]/div/div/a/i')
        common.wait_element(self.browser, f'//th[contains(.,"{column_name}")]//a[text()="To all claims"]')
        self.browser.click_element_when_visible(f'//th[contains(.,"{column_name}")]//a[text()="To all claims"]')

    def check_and_update_billing_medicaid(self, valid_billing: str, full_billing_name: str, location: str):
        all_billings = self.browser.find_elements('//a[contains(@data-bind, "billingName")]')

        first_billing = str(all_billings[0].text)
        is_valid = True
        for billing in all_billings:
            if valid_billing.lower() not in str(billing.text).lower() \
                    or first_billing.lower() != str(billing.text).lower():
                is_valid = False
                break

        if is_valid:
            self.browser.click_element_when_visible('//a[contains(@data-bind, "billingName")]')
            common.wait_element(self.browser, '//span[text()="EPSDT"]/../span[1]')
            current_location = str(self.browser.get_text('//span[text()="EPSDT"]/../span[1]'))
            # Close pop-up
            self.browser.click_element('//th[contains(.,"Billing")]')
            if current_location.strip().lower() != location.strip().lower():
                is_valid = False

        if not is_valid:
            self.change_billing('Billing', full_billing_name)

    def change_location(self, city: str, location_name: str):
        combined_location = '{} {}'.format(city, location_name)
        self.browser.click_element_when_visible('//th[contains(.,"Location")]/div/a[contains(@data-bind, "{title: \'Search for different provider\'}")]')

        common.wait_element(self.browser, '//th[contains(.,"Location")]/div/div/input')
        self.browser.input_text_when_element_is_visible('//th[contains(.,"Location")]/div/div/input', combined_location)

        common.wait_element(self.browser, '//li/div[contains(.,"' + city + '") and not(contains(.,"prior to")) and not(contains(.,"old location"))]', timeout=15)
        all_valid_location = self.browser.find_elements('//li/div[contains(.,"' + city + '") and not(contains(.,"prior to")) and not(contains(.,"old location"))]')

        index_of_valid_location = 0
        last_id_location = 0
        for location in all_valid_location:
            regex = re.search(r'\(ID: (\d+)\)', location.text)
            if regex is not None and regex[1].isdigit():
                if int(regex[1]) > last_id_location:
                    last_id_location = int(regex[1])
                    index_of_valid_location = all_valid_location.index(location)
        all_valid_location[index_of_valid_location].click()
        self.sync_to_all_claims('Location')

    def find_and_update_location(self, client_id: str, location_name='Office') -> bool:
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])
        self.browser.go_to(
            'https://members.centralreach.com/#billingmanager/billing/?clientId={}&startdate={}&enddate={}'.format(
                client_id, self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d'))
        )

        common.wait_element(self.browser, '//em[contains(., "ID: ' + client_id + '")]')
        location = self.get_client_location(client_id, '')

        self.browser.reload_page()
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[0])
        if len(location) == 0:
            common.log_message('ERROR: Location for client {} not found.'.format(client_id), 'ERROR')
            return False
        else:
            self.change_location(location, location_name)

    def check_and_update_location(self, client_id: str, insurance_name: str, location_name='Office') -> bool:
        all_locations = self.browser.find_elements('//a[contains(@data-bind, "locationName")]')
        index = -2
        any_not_valid_location = False
        last_location = ''
        is_two_different_location = False

        for location in all_locations:
            location_from_web = str(location.text).lower()
            if location_name.lower() in location_from_web and 'prior to' not in location_from_web \
                    and 'old location' not in location_from_web:
                if index == -2:
                    index = all_locations.index(location)
                if len(last_location) > 0 and last_location != location_from_web:
                    common.log_message('Found two different locations for client {}. Try to fix it.'.format(client_id))
                    is_two_different_location = True
                    break
                last_location = location_from_web
            else:
                any_not_valid_location = True

        if index == -2 or is_two_different_location:
            self.find_and_update_location(client_id, location_name)
        elif any_not_valid_location:
            if 'United Behavioral Health'.lower() == insurance_name.lower().strip():
                self.find_and_update_location(client_id, location_name)
            else:
                sync_all = self.browser.find_elements('//a[contains(@data-bind, "syncField") and @data-syncfield="location"]')
                sync_all[index].click()

        return True

    def update_claims_address(self, list_of_claims_url: list):
        for claim_url in list_of_claims_url:
            claim_id = claim_url.split('=')[-1]
            try:
                browser_tabs = self.browser.get_window_handles()
                self.browser.switch_window(browser_tabs[1])
                self.browser.go_to('https://members.centralreach.com/#claims/editor/?claimId={}'.format(claim_id))

                common.wait_element(self.browser, '//button[contains(., "Save Claim")]')
                self.browser.click_element_when_visible('//span[text()="Claim"]')
                common.wait_element(self.browser, '//input[@id="info-details-accountnumber"]')
                self.browser.input_text_when_element_is_visible('//input[@id="info-details-accountnumber"]', claim_id)
                self.browser.click_element_when_visible('//span[text()="Providers"]')
                common.wait_element(self.browser, '//input[@id="providers-billing-address1"]')
                self.browser.input_text_when_element_is_visible('//input[@id="providers-billing-address1"]',
                                                                'PO Box 8476 Pasadena, CA 91109-8476')
                self.browser.click_element_when_visible('//button[contains(., "Save Claim")]')
            except Exception as e:
                print('ERROR in update_claims_address(): {}. Claim ID {}'.format(str(e), claim_id))
                self.browser.capture_page_screenshot(
                    os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()),
                                 'output',
                                 'Something_went_wrong_Claim_{}.png'.format(claim_id))
                )
            finally:
                browser_tabs = self.browser.get_window_handles()
                self.browser.switch_window(browser_tabs[0])

    def change_provider_by_id(self, column_name: str, provider_id: str) -> bool:
        if not self.search_provider_by_id(column_name, provider_id):
            return False
        else:
            self.sync_to_all_claims(column_name)
        return True

    def validate_prior_authorization(self, list_of_claims_url: list):
        for claim_url in list_of_claims_url:
            claim_id = claim_url.split('=')[-1]
            try:
                browser_tabs = self.browser.get_window_handles()
                self.browser.switch_window(browser_tabs[1])
                self.browser.go_to('https://members.centralreach.com/#claims/editor/?claimId={}'.format(claim_id))

                common.wait_element(self.browser, '//button[contains(., "Save Claim")]')

                self.browser.click_element_when_visible('//span[text()="Claim"]')

                common.wait_element(self.browser, '//input[contains(@data-bind, "priorAuthorization")]')
                try_count = 0
                prior_authorization = ''
                while not prior_authorization and try_count < 4:
                    try_count += 1
                    try:
                        prior_authorization = str(self.browser.find_element('//input[contains(@data-bind, "priorAuthorization")]').get_property('value'))
                    except:
                        time.sleep(1)
                if '*' in prior_authorization:
                    self.browser.input_text('//input[contains(@data-bind, "priorAuthorization")]', prior_authorization.replace('*', '0'))
                    self.browser.click_element_when_visible('//button[contains(., "Save Claim")]')
            except Exception as e:
                print("ERROR in :validate_prior_authorization(): {}. Claim ID {}".format(str(e), claim_id))
                self.browser.capture_page_screenshot(
                    os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()),
                                 'output',
                                 'Something_went_wrong_Claim_{}.png'.format(claim_id))
                )
            finally:
                browser_tabs = self.browser.get_window_handles()
                self.browser.switch_window(browser_tabs[0])

    def is_valid_bcba_provider(self, client_id: str, insurance_name: str) -> bool:
        is_bcba_exist = False
        all_procedure_code = self.browser.find_elements(
            '//span[contains(@data-bind, "procedureCodeString() || procedureCode()")]')
        for procedure_code in all_procedure_code:
            if 'bcba' in str(procedure_code.text).lower():
                if 'United Behavioral Health'.lower() == insurance_name.lower().strip():
                    providers_all = self.browser.find_elements('//a[contains(@data-bind, "providerName")]')
                    provider_id = providers_all[all_procedure_code.index(procedure_code)].get_attribute('data-contactid')
                    is_bcba_exist = self.change_provider_by_id('Provider', provider_id)
                else:
                    sync_all = self.browser.find_elements('//a[contains(@data-bind, "syncField") and @data-syncfield="provider"]')
                    sync_all[all_procedure_code.index(procedure_code)].click()
                    is_bcba_exist = True
                break
        if not is_bcba_exist:
            is_bcba_exist = self.find_domo_provider_id_and_change(client_id, insurance_name)

        if is_bcba_exist:
            self.sync_provider_to_provider_supplier()
        return is_bcba_exist

    def prepare_claims_to_generate(self,
                                   insurance_name: str,
                                   client_id: str,
                                   location: str,
                                   list_of_providers=None
                                   ) -> bool:
        insurance_name = insurance_name.lower()
        if 'Macomb County Community Mental Health'.lower() in insurance_name:
            return False

        # Check and update provider field
        if 'Tricare'.lower() in insurance_name or 'Humana'.lower() in insurance_name:
            self.browser.select_checkbox('//input[contains(@data-bind, "includeTimes")]')
            self.browser.select_checkbox('//input[contains(@data-bind, "splitProviders")]')
            self.browser.unselect_checkbox('//input[contains(@data-bind, "useServiceLocation")]')
            self.clear_provider_supplier()
        elif 'Cigna'.lower() in insurance_name:
            if self.sync_provider_supplier_fields():
                self.sync_provider_supplier_to_provider()
            elif self.find_domo_provider_id_and_change(client_id, insurance_name):
                self.sync_provider_to_provider_supplier()
            else:
                return False
        else:
            if not self.is_valid_bcba_provider(client_id, insurance_name):
                return False

        # Check pointer and DX code
        for i in range(2, 5):
            pointers = self.browser.find_elements('//input[@data-bind="value: diagPointer{}"]'.format(i))
            for p in pointers:
                if p.get_property('value'):
                    p.send_keys('\ue003\ue003\ue003\ue003\ue003')
        pointer = self.browser.find_elements('//input[@data-bind="value: diagPointer1"]')
        for p in pointer:
            if p.get_property('value') != '1':
                p.send_keys('\ue003\ue003\ue003\ue003\ue0031')
        pointer[0].click()
        if not self.browser.does_page_contain_element('//b[text()="Diag Codes:"]/../a/span[contains(@data-bind, "removeDiagnosisCode")]/..'):
            common.log_message("ERROR: Diagnosis code not exist for client {}".format(client_id), 'ERROR')
            return False

        # Add modifier if modifiers_check()
        if list_of_providers is not None:
            modifier_key = '76'
            start_index = 1
            if len(list_of_providers) > 1 and ('Humana'.lower() in insurance_name.lower() or
                                               'Tricare'.lower() in insurance_name.lower()):
                modifier_key = '77'
                start_index = 0
            modifiers = self.browser.find_elements('//input[@data-bind="value: modifier1"]')
            for index in range(start_index, len(modifiers)):
                if len(modifiers[index].get_property('value')) == 0:
                    modifiers[index].send_keys(modifier_key)
                else:
                    for j in range(2, 5):
                        modifiers_next = self.browser.find_elements('//input[@data-bind="value: modifier{}"]'.format(str(j)))
                        if len(modifiers_next[index].get_property('value')) == 0:
                            modifiers_next[index].send_keys(modifier_key)
                            break
            modifiers[0].click()
            common.log_message('Modifier {} applied for client ID {}'.format(modifier_key, client_id))

        # Check and update billing and location fields
        if 'CO Medicaid'.lower() in insurance_name:
            self.clear_location()
            self.check_and_update_billing_medicaid('EPSDT', location + ' EPSDT', location)
        else:
            self.check_and_update_billing('T. Health', 'Trumpet Behavioral Health')
            if not self.check_and_update_location(client_id, insurance_name):
                return False

        self.clear_referrer()
        return True

    def start_claims_generation(self):
        self.browser.click_element_when_visible('//a[text()="Combined Claims View"]')
        common.wait_element(self.browser, '//li[@class="active"]/a[text()="Combined Claims View"]')

        self.browser.click_element_when_visible('//button[contains(., "Start claims generation")]')
        common.wait_element(self.browser, '//a[contains(.,"Go to claims inbox") and contains(@data-bind, "visible: $root.bulkClaimsVm.processingComplete()")]')

    def post_claims_generation_and_apply_label(self, insurance_name: str, client: Client) -> list:
        list_of_claims_url = []
        claims = self.browser.find_elements('//a[contains(@data-bind, "&&claimId()!=-1")]')
        for item in claims:
            if item.is_displayed():
                list_of_claims_url.append(item.get_attribute('href'))

        # check claims
        if 'Cigna'.lower() in insurance_name or 'Contra Costa'.lower() in insurance_name \
                or 'Beacon Line Construction Benefit Fund'.lower() in insurance_name:
            if len(list_of_claims_url) > 0:
                if 'Contra Costa'.lower() in insurance_name \
                        or 'Beacon Line Construction Benefit Fund'.lower() in insurance_name:
                    self.update_claims_address(list_of_claims_url)
                elif 'Cigna'.lower() in insurance_name:
                    self.validate_prior_authorization(list_of_claims_url)

        list_of_claims_id: list = []
        for claim_url in list_of_claims_url:
            claim_id = claim_url.split('=')[-1]
            if self.send_to_gateway(client.client_id, insurance_name, claim_id):
                list_of_claims_id.append(claim_id)
                common.log_message(f'Claim {claim_id} was sent to the gateway')
        return list_of_claims_id

    @staticmethod
    def grouping_of_overlap(timesheets: list) -> dict:
        overlaped = {}
        for i in range(len(timesheets)):
            for n in range(i + 1, len(timesheets)):
                if timesheets[i].check_overlap(timesheets[n]):
                    if timesheets[i] not in overlaped:
                        overlaped[timesheets[i]] = []
                    overlaped[timesheets[i]].append(timesheets[n])
        return overlaped

    def validate_cd_number(self, temp_table: Table, timesheet: Timesheet, fee_schedule_name: str):
        # Check if Cd number exist in mapping file
        cd_number_first = temp_table.copy()
        condition = lambda x: str(x).replace('.0', '').strip().lower() == timesheet.service_code.strip().lower()
        cd_number_first.filter_by_column(self.mapping.fee_schedule_columns_index['CdNum'], condition)
        if len(cd_number_first) == 0:
            raise ValueError('Cd number {} not found in mapping'.format(timesheet.service_code))

        row_first = None
        if len(cd_number_first) > 1:
            same_row_test = cd_number_first[0]
            index_can_overlap = self.mapping.fee_schedule_columns_index['Can Overlap']
            index_cannot_overlap = self.mapping.fee_schedule_columns_index['Cannot Overlap']
            for row in range(len(cd_number_first)):
                if str(cd_number_first[row][self.mapping.fee_schedule_columns_index['CdDscrpt']]).strip().lower() in \
                        timesheet.service_dscrpt.strip().lower():
                    row_first = cd_number_first[row]
                    break
                if str(same_row_test[index_can_overlap]).strip().lower() != str(
                        cd_number_first[row][index_can_overlap]).strip().lower():
                    same_row_test = None
                if str(same_row_test[index_cannot_overlap]).strip().lower() != str(
                        cd_number_first[row][index_cannot_overlap]).strip().lower():
                    same_row_test = None
            if row_first is None and same_row_test is not None:
                row_first = same_row_test
        else:
            row_first = cd_number_first[0]
        if row_first is None:
            raise ValueError(
                'CdNum {} not found in mapping file for payor {}'.format(timesheet.service_code, fee_schedule_name))
        return row_first

    def check_2_to_1(self, key_timesheet: Timesheet, payor: str, fee_schedule_name: str) -> bool:
        # Check SCA sheet - 2 to 1 okay
        if key_timesheet.client.client_id.lower() in self.mapping.sca and \
                (payor.lower() in self.mapping.sca.values() or fee_schedule_name.lower() in self.mapping.sca.values()):
            # print('SUCCESS: Client {} in "2 to 1 okay" list. Overlap permitted for payor {}'.format(key_timesheet.client, fee_schedule_name))
            return True
        return False

    def is_valid_provider_tag(self, timesheet: Timesheet, tag: str) -> bool:
        try:
            browser_tabs = self.browser.get_window_handles()
            self.browser.switch_window(browser_tabs[1])

            self.apply_filter(self.filter_secondary_claims, f'&billingEntryId={timesheet.timesheet_id}')
            common.wait_element(self.browser, f'//em[contains(., "{timesheet.timesheet_id}")]')

            provider_id: str = self.browser.get_element_attribute(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]//a[@data-title="Click to filter by this provider"]/../a[2]', 'contactid')

            self.browser.scroll_element_into_view('//a[@contactid="' + provider_id + '"]')
            self.browser.click_element_when_visible('//a[@contactid="' + provider_id + '"]')
            common.wait_element(self.browser, '//small[text()="Upload File"]')
            common.wait_element(self.browser, '//a[text()=" Labels"]', timeout=10)
            if self.browser.does_page_contain_element('//a[text()=" Labels"]'):
                self.browser.click_element_when_visible('//a[text()=" Labels"]')
                time.sleep(0.5)

            common.wait_element(self.browser, '//span[@class="tag-name"]')
            labels: list = self.browser.find_elements('//span[@class="tag-name"]')
            current_provider_labels: list = []
            for label in labels:
                if str(label.text):
                    current_provider_labels.append(str(label.text).strip().lower())
            return tag.lower() in current_provider_labels
        except Exception as ex:
            common.log_message('is_valid_provider_tag(): ' + str(ex))
        finally:
            browser_tabs = self.browser.get_window_handles()
            self.browser.switch_window(browser_tabs[0])
        return False

    def does_timesheet_overlapped(self, timesheets: list) -> bool:
        overlaped = self.grouping_of_overlap(timesheets)

        for key_timesheet, grouped_timesheets in overlaped.items():
            try:
                payor = str(key_timesheet.current_payor).strip()
                # Check if payor exist in mapping file
                if payor.lower() not in self.mapping.payor_mapping:
                    raise ValueError('Payor {} not found in mapping'.format(payor))

                # Check if fee schedule name exist in mapping file and filter table
                fee_schedule_name = str(self.mapping.payor_mapping[payor.lower()]).strip()
                # CR from customer
                if fee_schedule_name.lower() == 'Managed Health Network'.lower() and key_timesheet.service_code == '96152':
                    return True

                temp_table = self.mapping.fee_schedule_table.copy()
                temp_table.filter_by_column(self.mapping.fee_schedule_columns_index['FeeSched'], lambda x: str(x).strip().lower() == fee_schedule_name.lower())
                if len(temp_table) == 0:
                    raise ValueError('Fee schedule not contain {} value'.format(fee_schedule_name))
                row_key = self.validate_cd_number(temp_table, key_timesheet, fee_schedule_name)
                number_key = key_timesheet.cd_number.lower()
                can_key = str(row_key[self.mapping.fee_schedule_columns_index['Can Overlap']]).strip().lower()
                for grouped_timesheet in grouped_timesheets:
                    # Validate cd numbers
                    if fee_schedule_name.lower() == 'Managed Health Network'.lower() and grouped_timesheet.cd_number == '96152':
                        return True
                    row_grouped = self.validate_cd_number(temp_table, grouped_timesheet, fee_schedule_name)
                    number_grouped = grouped_timesheet.cd_number.lower()

                    can_grouped = str(row_grouped[self.mapping.fee_schedule_columns_index['Can Overlap']]).strip().lower()
                    if number_key in str(row_grouped[self.mapping.fee_schedule_columns_index['Cannot Overlap']]) or \
                            number_grouped in str(row_key[self.mapping.fee_schedule_columns_index['Cannot Overlap']]):
                        if self.check_2_to_1(key_timesheet, payor, fee_schedule_name):
                            continue
                    elif (number_key in can_grouped or can_grouped == 'all' or 'all remaining' in can_grouped) or \
                            (number_grouped in can_key or can_key == 'all' or 'all remaining' in can_key):
                        if 'if provider is' in can_key or 'if provider is' in can_grouped:
                            valid_tag = re.findall(r'provider is (\w+)(,|$)', can_key)
                            temp_timesheet: Timesheet = key_timesheet
                            if not valid_tag:
                                valid_tag = re.findall(r'provider is (\w+)(,|$)', can_grouped)
                                temp_timesheet: Timesheet = grouped_timesheet
                            if valid_tag:
                                provider_tag = valid_tag[0][0]
                                if self.is_valid_provider_tag(temp_timesheet, provider_tag):
                                    continue
                        else:
                            continue
                    else:
                        if self.check_2_to_1(key_timesheet, payor, fee_schedule_name):
                            continue
                    common.log_message(
                        'OVERLAP: Client {} [{}]. Overlap {} and {} not permitted for {}'.format(
                            key_timesheet.client,
                            key_timesheet.client_id,
                            key_timesheet.cd_number,
                            grouped_timesheet.cd_number,
                            fee_schedule_name)
                    )
                    return True
            except Exception as ex:
                common.log_message('ERROR: {}'.format(str(ex)), 'ERROR')
                common.log_message(key_timesheet, 'ERROR')
                for grouped_timesheet in grouped_timesheets:
                    print(grouped_timesheet)
                return True
        return False

    @staticmethod
    def does_location_difference(timesheets: list) -> list or None:
        location_check: dict = {}
        provider_check: dict = {}
        for timesheet in timesheets:
            if timesheet.service_code not in location_check:
                location_check[timesheet.service_code] = []
                provider_check[timesheet.service_code] = []
            if timesheet.location not in location_check[timesheet.service_code]:
                location_check[timesheet.service_code].append(timesheet.location)
            if timesheet.provider.provider_id not in provider_check[timesheet.service_code]:
                provider_check[timesheet.service_code].append(timesheet.provider.provider_id)
            if len(location_check[timesheet.service_code]) > 1:
                return provider_check[timesheet.service_code]
        return None

    def generate_secondary_claim_hard_way(self, timesheets: list) -> bool:
        self.select_rows(timesheets)

        list_of_providers = None
        if len(timesheets) > 1:
            if self.does_timesheet_overlapped(timesheets):
                self.select_rows_and_apply_label(timesheets, 'Overlapped CPT Codes')
                return False
            list_of_providers = self.does_location_difference(timesheets)

        insurance_name: str = timesheets[0].current_payor
        client: Client = timesheets[0].client

        self.bulk_merge_claims(insurance_name)

        if not self.prepare_claims_to_generate(insurance_name, client.client_id, client.location_city, list_of_providers):
            self.browser.click_element_when_visible('//div/ul/li/a[text()="Billing"]')
            self.browser.reload_page()
            return False

        '''
        # It looks like a modifier is automatically added with this method of generating claims
        processed_service_code: list = []
        for timesheet in timesheets:
            if timesheet.modifiers and timesheet.service_code not in processed_service_code:
                processed_service_code.append(timesheet.service_code)
                mod_list: list = timesheet.modifiers.split(',')
                for mod in mod_list:
                    modifiers = self.browser.find_elements(f'//span[contains(., "{timesheet.service_code}")]/../..//input[@data-bind="value: modifier1"]')
                    for index in range(0, len(modifiers)):
                        if len(modifiers[index].get_property('value')) == 0:
                            modifiers[index].send_keys(mod)
                        else:
                            for j in range(2, 5):
                                modifiers_next = self.browser.find_elements(f'//span[contains(., "{timesheet.service_code}")]/../..//input[@data-bind="value: modifier{str(j)}"]')
                                if len(modifiers_next[index].get_property('value')) == 0:
                                    modifiers_next[index].send_keys(mod)
                                    break
                    modifiers[0].click()
        if processed_service_code:
            time.sleep(2)
        '''

        # click start claims generation
        self.start_claims_generation()
        common.log_message(f'Claim generated successfully. Client: { client.client_id }')

        list_of_claims_id: list = self.post_claims_generation_and_apply_label(insurance_name.lower(), client)

        self.browser.click_element_when_visible('//div/ul/li/a[text()="Billing"]')
        self.browser.wait_until_element_is_not_visible('//div/ul/li/a[text()="Billing"]')

        self.unselect_rows(timesheets)
        if not list_of_claims_id:
            return False
        timesheets[0].claim_id = list_of_claims_id[0]
        return True

    @staticmethod
    def get_client(client_name: str, client_id: str) -> Client:
        if client_id in Client.clients:
            return Client.clients[client_id]
        return Client(client_name, client_id)

    def get_provider(self, provider_name: str, provider_id: str) -> Provider:
        if provider_id in Provider.providers:
            provider: Provider = Provider.providers[provider_id]
        else:
            provider: Provider = Provider(provider_name, provider_id)
        return provider

    def get_provider_and_tags(self, provider_name: str, provider_id: str) -> Provider:
        if provider_id in Provider.providers:
            provider: Provider = Provider.providers[provider_id]
        else:
            provider: Provider = Provider(provider_name, provider_id)

        if provider.tags:
            return provider

        self.browser.scroll_element_into_view('//a[@contactid="' + provider_id + '"]')
        self.browser.click_element_when_visible('//a[@contactid="' + provider_id + '"]')
        common.wait_element(self.browser, '//small[text()="Upload File"]')
        common.wait_element(self.browser, '//a[text()=" Labels"]', timeout=10)
        if self.browser.does_page_contain_element('//a[text()=" Labels"]'):
            self.browser.click_element_when_visible('//a[text()=" Labels"]')
            time.sleep(0.5)

        common.wait_element(self.browser, '//span[@class="tag-name"]')
        labels = self.browser.find_elements('//span[@class="tag-name"]')
        for label in labels:
            if str(label.text):
                provider.tags.append(str(label.text).strip())

        provider.full_location_info = self.browser.get_text('//div[@id="contactcard-addresses"]')
        return provider

    def prepare_secondary_claim(self, timesheet: Timesheet, timesheets: list, current_url: str) -> bool:
        columns: list = self.browser.find_elements(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td')
        if not columns:
            print('_columns index')
            self.browser.reload_page()
            common.wait_element(self.browser, f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td', is_need_screen=False)
            columns: list = self.browser.find_elements(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td')
        timesheet.location = str(columns[self.headers_index['location']].text)
        provider_id: str = self.browser.get_element_attribute('//a[text()="{}"]'.format(columns[self.headers_index['providers']].text), 'contactid')
        timesheet.provider = self.get_provider_and_tags(str(columns[self.headers_index['providers']].text), provider_id)

        timesheet.current_payor = str(columns[self.headers_index['payor']].text)
        if timesheet.current_payor[3:].strip().lower() not in self.mapping.payor_mapping:
            self.select_rows_and_apply_label([timesheet], 'Non Insurance Payers')
            return False

        timesheet.set_date_and_time(columns[self.headers_index['date']].text, columns[self.headers_index['time']].text)
        if not self.is_flip_primary_to_secondary(timesheet):
            self.select_rows_and_apply_label([timesheet], 'Expired Secondary Insurance')
            return False

        # Check agreed rate
        payor_from_web: str = str(columns[self.headers_index['payor']].text)
        if payor_from_web.startswith('S:'):
            timesheet.current_payor = payor_from_web[3:]
        else:
            timesheet.current_payor = payor_from_web.split(':')[1].strip().replace(' >', ':')

        timesheet.set_service(str(columns[self.headers_index['service/auth']].text).strip())
        if timesheet.service_code == '97156' and 'CO Medicaid'.lower() in timesheet.current_payor.lower():
            self.select_rows_and_apply_label([timesheet], 'WO')
            return False

        agreed_rate: float = self.get_agreed_rates(timesheet)
        agreed_rate_from_web: str = str(columns[self.headers_index['agreed']].text).strip()
        if agreed_rate and '%.2f' % agreed_rate != agreed_rate_from_web:
            is_success: bool = self.update_agreed_rate('%.2f' % agreed_rate, timesheet.timesheet_id)
            common.wait_element(self.browser, '//th[contains(.,"Payor")]/a/i', 10)
            if not self.browser.does_page_contain_element('//th[contains(.,"Payor")]/a/i'):
                self.browser.go_to(current_url)
            self.browser.reload_page()
            common.wait_element(self.browser, '//th[contains(.,"Payor")]/a/i', 45)
            if not is_success:
                common.log_message(f"Cannot save Timesheet {timesheet.timesheet_id}")
        elif not agreed_rate:
            if 'Aetna'.lower() in timesheet.primary_payor.payer_name.lower() \
                    or 'Magellan'.lower() in timesheet.primary_payor.payer_name.lower() \
                    or 'Tricare'.lower() in timesheet.primary_payor.payer_name.lower() \
                    or 'Cigna'.lower() in timesheet.primary_payor.payer_name.lower():
                common.log_message(f'Primary insurance is {timesheet.primary_payor.payer_name}')
            else:
                self.select_rows_and_apply_label([timesheet], 'Unknown Agreed Rates')
                return False
        common.log_message(f'Agreed rate: {"%.2f" % agreed_rate}. Agreed rate from web: {agreed_rate_from_web}')

        common.wait_element(self.browser, f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td[{self.headers_index["owed"] + 1}]')
        timesheet.owed = float(str(self.browser.find_element(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td[{self.headers_index["owed"] + 1}]').text).replace(',', ''))
        timesheet.payment_count = int(self.get_payment_count(timesheet.timesheet_id))

        common.log_message(f'Timesheet ID: {timesheet.timesheet_id}. Date of service: {timesheet.date}. How many payments: {timesheet.payment_count}')
        if timesheet.payment_count == 0 or timesheet.owed == .0:
            self.select_rows_and_apply_label([timesheet], 'No Payment')
            return False
        if timesheet.owed < .0:
            self.select_rows_and_apply_label([timesheet], 'Sales adjustment')
            return False
        timesheet.secondary_claim = self.check_secondary_claim(timesheet.timesheet_id)
        return True

    def check_secondary_claim(self, timesheet_id) -> bool:
        secondary_available: bool = False
        self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/div/button')
        self.browser.click_element_when_visible(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/div/button')

        common.wait_element(self.browser, f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/div//li[contains(., "Claims Generated")]', timeout=10, is_need_screen=False)
        if self.browser.does_page_contain_element(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/div//li[contains(., "Claims Generated")]'):
            secondary_available = True
        self.browser.reload_page()
        return secondary_available

    def secondary_claims_processing(self, input_client: str) -> None:
        self.apply_filter(self.filter_secondary_claims, '&pageSize=750')
        if self.is_no_results('No results matched {} filter and date range'.format(self.filter_secondary_claims)):
            return

        self.open_window_with_clients()
        valid_clients: list = self.get_list_of_clients()
        self.browser.reload_page()
        self.open_window_with_clients()

        # close left side menu
        if self.browser.does_page_contain_element('//a[@data-click="closeMenu"]') and \
                self.browser.find_element('//a[@data-click="closeMenu"]').is_displayed():
            self.browser.click_element_when_visible('//a[@data-click="closeMenu"]')

        self.headers_index = self.find_header_index(
            ['client', 'date', 'time', 'providers', 'payor', 'service/auth', 'location', 'agreed', 'paid', 'owed', 'options']
        )

        for client_name in valid_clients:
            if client_name.strip().lower() != input_client.strip().lower():
                continue
            try:
                client_id = self.select_client_from_list(client_name)
                common.log_message(f'Start of client processing: {client_name} ({client_id})')
                if self.browser.does_page_contain_element('//div[text()="No results matched your keywords, filters, or date range" and not(@style="display: none;")]'):
                    common.log_message(f'ERROR: No rows found for {client_name} client')
                    continue

                timesheets_by_date: dict = self.get_timesheets_for_processing()
                timesheets_filters_free: dict = self.get_timesheets_data_filters_free(client_id)
                current_url: str = self.browser.get_location()
                for date, timesheets in timesheets_by_date.items():
                    is_failed: bool = False
                    common.log_message('--------------------------------------------------------------------')
                    for timesheet in timesheets:
                        try:
                            common.log_message(f'Start of timesheet processing: { timesheet.timesheet_id }')

                            timesheet.client = self.get_client(client_name, client_id)
                            time.sleep(.5)
                            if not self.prepare_secondary_claim(timesheet, timesheets, current_url):
                                continue

                            common.wait_element(self.browser, f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td[contains(@class, "charge") and not(contains(@data-bind,"useAgreedView()"))]')
                            timesheet.billed = float(self.browser.get_text(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td[contains(@class, "charge") and not(contains(@data-bind,"useAgreedView()"))]').replace(',', ''))
                            timesheet.amount_paid = float(self.browser.get_text(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td/span[contains(@data-bind, "amountPaid")]').replace(',', ''))
                        except Exception as timesheet_error:
                            timesheet.is_valid = False
                            common.log_message('Timesheet processing error: ' + str(timesheet_error), 'ERROR')
                            self.browser.capture_page_screenshot(os.path.join(
                                os.environ.get("ROBOT_ROOT", os.getcwd()),
                                'output',
                                f'Something_went_wrong_Timesheet_{timesheet.timesheet_id}.png')
                            )

                            common.log_message('ERROR: {} processing failed. Something went wrong.'.format(timesheet.timesheet_id), 'ERROR')
                            traceback.print_exc()

                            if self.browser.does_page_contain_element('//div/ul/li/a[text()="Billing"]'):
                                if self.browser.find_element('//div/ul/li/a[text()="Billing"]').is_displayed():
                                    self.browser.click_element_when_visible('//div/ul/li/a[text()="Billing"]')
                            self.browser.reload_page()

                            browser_tabs = self.browser.get_window_handles()
                            self.browser.switch_window(browser_tabs[0])
                            self.browser.go_to(current_url)
                        finally:
                            if not timesheet.is_valid:
                                is_failed = True
                    if is_failed:
                        continue

                    current_timesheet: Timesheet = timesheets[0]
                    try:
                        if not current_timesheet.client.is_insurance_details_scraped:
                            self.get_insurance_details(current_timesheet.client)
                            current_timesheet.client.is_insurance_details_scraped = True
                        client: Client = current_timesheet.client
                        if 'CO Medicaid'.lower() in current_timesheet.current_payor.lower():
                            client.location_city = self.get_client_location(client.client_id, 'CO Medicaid')

                        is_hard_way: bool = False
                        eob: dict = {}
                        # Macro 3
                        if current_timesheet.secondary_claim:
                            common.log_message('Generate Secondary Claim Easy Way')
                            eob: dict = self.waystar.get_eob_data(timesheets[0].client.client_name, timesheets[0].date_of_service)
                            if not self.does_amount_match(timesheets, timesheets_filters_free[date], eob):
                                continue
                            policy_id: str = self.generate_secondary_claim(timesheets)
                            if policy_id:
                                if not self.populate_provider_tab(timesheets, policy_id):
                                    self.select_rows_and_apply_label(timesheets, 'Non Credentialed Provider')
                                    continue
                                if not self.check_service_code(timesheets):
                                    common.log_message('Cannot change service code')
                                    continue
                                self.fix_claim_validation_errors()
                                self.save_and_move_to_inbox()
                                if not self.send_to_gateway(current_timesheet.client.client_id, current_timesheet.current_payor, current_timesheet.claim_id):
                                    continue
                                self.waystar.edit_waystar_claim(current_timesheet.claim_id, current_timesheet, timesheets, eob)
                                if self.waystar.does_claim_rejected(current_timesheet.claim_id):
                                    self.select_rows_and_apply_label(timesheets, 'Rejected Waystar')
                                    continue
                                self.select_rows_and_apply_label(timesheets, '2CSELEC', '2ND')
                                common.log_message('Timesheets successfully processed')
                            else:
                                is_hard_way = True
                        else:
                            is_hard_way = True

                        if is_hard_way:
                            common.log_message('Generate Secondary Claim Hard Way')
                            if not self.generate_secondary_claim_hard_way(timesheets):
                                common.log_message(f'Processing failed. Cannot generate a claim. Timesheet: {current_timesheet.timesheet_id}')
                                continue
                            if self.waystar.does_claim_rejected(current_timesheet.claim_id):
                                if not self.waystar.edit_waystar_claim(current_timesheet.claim_id, current_timesheet, timesheets, eob):
                                    self.select_rows_and_apply_label(timesheets, 'Rejected Waystar')
                                    continue
                                if self.waystar.does_claim_rejected(current_timesheet.claim_id):
                                    self.select_rows_and_apply_label(timesheets, 'Rejected Waystar')
                                else:
                                    self.select_rows_and_apply_label(timesheets, '2CSELEC', '2ND')
                            else:
                                self.select_rows_and_apply_label(timesheets, '2CSELEC', '2ND')
                    except Exception as timesheet_error:
                        common.log_message('Macro 3-5 error: ' + str(timesheet_error), 'ERROR')
                        self.browser.capture_page_screenshot(os.path.join(
                            os.environ.get("ROBOT_ROOT", os.getcwd()),
                            'output',
                            f'Something_went_wrong_{current_timesheet.timesheet_id}.png')
                        )

                        common.log_message(f'ERROR: {current_timesheet.timesheet_id} processing failed. Something went wrong.', 'ERROR')
                        traceback.print_exc()

                        if self.browser.does_page_contain_element('//div/ul/li/a[text()="Billing"]'):
                            if self.browser.find_element('//div/ul/li/a[text()="Billing"]').is_displayed():
                                self.browser.click_element_when_visible('//div/ul/li/a[text()="Billing"]')
                        self.browser.reload_page()

                        browser_tabs = self.browser.get_window_handles()
                        self.browser.switch_window(browser_tabs[0])
            except Exception as client_error:
                common.log_message('client_error(): ' + str(client_error), 'ERROR')
                common.log_message('ERROR: {} processing failed. Something went wrong.'.format(client_name), 'ERROR')
                self.browser.capture_page_screenshot(os.path.join(
                    os.environ.get("ROBOT_ROOT", os.getcwd()),
                    'output',
                    'Something_went_wrong_{}.png'.format(str(client_name).replace('"', '').replace("'", "")))
                )
                traceback.print_exc()
                browser_tabs = self.browser.get_window_handles()
                self.browser.switch_window(browser_tabs[0])
                self.apply_filter(self.filter_secondary_claims, '&pageSize=750')
