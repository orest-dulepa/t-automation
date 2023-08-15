from RPA.Browser.Selenium import Selenium
from libraries import common
from urllib.parse import urlparse
import datetime
import time
import os
import shutil
import re
from libraries.excel import ExcelInterface
from libraries.waystar import WayStar
from libraries.models.timesheet import Timesheet
import traceback


class CentralReach:
    filter_name = 'Patient Responsibility'
    list_of_non_insurance = ['None', 'School District', 'California Regional Center', 'Private Pay']

    def __init__(self, credentials: dict):
        self.browser: Selenium = Selenium()
        self.browser.timeout = 60
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.path_to_temp = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'cr')
        self.base_url = self.get_base_url()
        self.login_to_central_reach()

        self.start_date: datetime = None
        self.end_date: datetime = None

        self.mapping: ExcelInterface = None

        self.headers_index: dict = {}

        self.waystar: WayStar = None

    def get_base_url(self):
        parsed_uri = urlparse(self.url)
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

    def login_to_central_reach(self):
        self.browser.close_browser()
        self.is_site_available = False
        count = 1

        if os.path.exists(self.path_to_temp):
            shutil.rmtree(self.path_to_temp)
        os.mkdir(self.path_to_temp)
        self.browser.set_download_directory(self.path_to_temp, True)

        while count <= 3 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.url)
                self.browser.set_window_size(1920, 1080)
                self.browser.maximize_browser_window()
                common.wait_element(self.browser, "//input[@type='password']", is_need_screen=False, timeout=10)
                if self.browser.does_page_contain_element("//p[text()='Scheduled Maintenance']"):
                    if self.browser.find_element("//p[text()='Scheduled Maintenance']").is_displayed():
                        common.log_message("Logging into CentralReach failed. Scheduled Maintenance.".format(count), 'ERROR')
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
        start_date = datetime.datetime.strptime('1/1/2019', '%m/%d/%Y')
        end_date = datetime.datetime.utcnow() + datetime.timedelta(days=-14)

        print('Start date: {}. End date: {}'.format(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        return start_date, end_date

    def apply_filter(self, filter_name: str, additional_params='', sort_by_client=False):
        # Go to billing page
        self.browser.go_to(self.base_url + '#billingmanager/billing/?startdate={}&enddate={}'.format(
            self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d')))
        common.wait_element(self.browser, '//th[contains(.,"Payor")]/a/i')

        if self.browser.does_page_contain_element('//li/a[@data-click="openMenu"]'):
            if self.browser.find_element('//li/a[@data-click="openMenu"]').is_displayed():
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
        common.wait_element(self.browser, header_selector)
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

    @staticmethod
    def does_need_skip_insurance(insurance_name: str) -> bool:
        insurance_name = insurance_name.lower()
        if 'Macomb County Community Mental Health'.lower() in insurance_name:
            return True
        if 'Rocky Mountain Health Plans'.lower() in insurance_name and 'CYMHTA'.lower() in insurance_name:
            return True
        if 'None'.lower() == insurance_name:
            return True
        if 'School District'.lower() in insurance_name:
            return True
        if 'California Regional Center'.lower() in insurance_name:
            return True
        if 'Private Pay'.lower() in insurance_name:
            return True

        return False

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

    def is_click_next_clients_page(self, window_title: str) -> bool:
        selector_next_element = f'//div/span[text()="{window_title}"]/../../div/ul/li/a[@data-bind="visible: canPageUp"]'

        if self.browser.does_page_contain_element(selector_next_element):
            if self.browser.find_element(selector_next_element).is_displayed():
                self.browser.click_element_when_visible(selector_next_element)
                self.browser.wait_until_element_is_not_visible(f'//div/span[text()="{window_title}"]/../../div/div[@data-bind="visible: loading()"]')
                return True
            else:
                return False
        else:
            return False

    def get_list_of_clients(self) -> list:
        self.open_window_with_clients()

        full_list_of_valid_clients: list = self.get_list_of_clients_from_current_page()

        while True:
            if self.is_click_next_clients_page('clients'):
                temp: list = self.get_list_of_clients_from_current_page()
                full_list_of_valid_clients += temp
            else:
                break

        return full_list_of_valid_clients

    def scroll_into_view_item(self, selector_for_click: str, selector_as_result: str, window_title: str) -> None:
        try:
            while not self.browser.does_page_contain_element(selector_for_click):
                if not self.is_click_next_clients_page(window_title):
                    return
            common.wait_element(self.browser, selector_for_click)
            self.browser.scroll_element_into_view(selector_for_click)
        except:
            pass
        finally:
            self.browser.click_element_when_visible(selector_for_click)
            common.wait_element(self.browser, selector_as_result)

    def select_client_from_list(self, client_name: str) -> str:
        if "'" in client_name:
            selector_client_name = '//a[contains(., "' + client_name + '") or contains(., "' + client_name.replace(' ', '  ') + '")]'
            selector_client_selected = '//em[contains(., "Client: ' + client_name + '") or contains(., "' + client_name.replace(' ', '  ') + '")]'
            self.scroll_into_view_item(selector_client_name, selector_client_selected, 'clients')
        else:
            selector_client_name = "//a[contains(., '" + client_name + "') or contains(., '" + client_name.replace(' ', '  ') + "')]"
            selector_client_selected = "//em[contains(., 'Client: " + client_name + "') or contains(., '" + client_name.replace(' ', '  ') + "')]"
            self.scroll_into_view_item(selector_client_name, selector_client_selected, 'clients')
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

    def select_rows(self, timesheets: list) -> None:
        for timesheet in timesheets:
            self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{ timesheet.timesheet_id }"]/td/input')
            self.browser.select_checkbox(f'//tr[@id="billing-grid-row-{ timesheet.timesheet_id }"]/td/input')

    def unselect_rows(self, timesheets: list) -> None:
        for timesheet in timesheets:
            self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{ timesheet.timesheet_id }"]/td/input')
            self.browser.unselect_checkbox(f'//tr[@id="billing-grid-row-{ timesheet.timesheet_id }"]/td/input')

    def get_payment_count(self, timesheet_id: str) -> str:
        self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/a[@data-title="Click to view or add payments"]')
        try:
            self.browser.click_element_when_visible(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/a[@data-title="Click to view or add payments"]')
        except:
            self.browser.execute_javascript('window.scrollBy(0, 42)')
            self.browser.click_element_when_visible(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/a[@data-title="Click to view or add payments"]')

        common.wait_element(self.browser, '(//span[text()=" Payments"])[last()]/span')
        payment_count: str = self.browser.get_text('(//span[text()=" Payments"])[last()]/span')

        self.browser.click_element_when_visible(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/a[@data-title="Click to view or add payments"]')
        self.browser.wait_until_element_is_not_visible('(//span[text()=" Payments"])[last()]/span')
        return payment_count

    def select_rows_and_apply_label(self, timesheets: list, label_add: str, label_remove: str = '') -> None:
        if not label_remove:
            timesheets_id: list = [timesheet.timesheet_id for timesheet in timesheets]
            common.log_message(f'ERROR: Label "{label_add}" applied to timesheet { ", ".join(timesheets_id) }')
            for timesheet in timesheets:
                timesheet.processed = True

        self.select_rows(timesheets)
        self.apply_label(label_add, label_remove)
        self.unselect_rows(timesheets)

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

    @staticmethod
    def is_all_processed(timesheets: list) -> bool:
        for timesheet in timesheets:
            if not timesheet.processed:
                return False
        return True

    @staticmethod
    def get_timesheets_by_service_code(timesheets: list) -> dict:
        timesheets_by_service_code: dict = {}

        for timesheet in timesheets:
            if timesheet.service_code not in timesheets_by_service_code:
                timesheets_by_service_code[timesheet.service_code] = []
            timesheets_by_service_code[timesheet.service_code].append(timesheet)
        return timesheets_by_service_code

    def get_combined_timesheets(self, timesheets: list) -> dict:
        timesheets_by_service_code: dict = self.get_timesheets_by_service_code(timesheets)
        result: dict = {}
        for service_code, timesheets in timesheets_by_service_code.items():
            for timesheet in timesheets:
                if service_code not in result:
                    result[service_code] = []
                result[service_code].append({
                    'billed': timesheet.billed,
                    'agreed': timesheet.agreed,
                    'timesheets': [timesheet],
                })

                temp_billed: float = timesheet.billed
                temp_agreed: float = timesheet.agreed
                temp_timesheets_id: list = [timesheet]
                for timesheet_temp in timesheets[timesheets.index(timesheet) + 1:]:
                    if len(timesheets[timesheets.index(timesheet) + 1:]) > 1:
                        result[service_code].append({
                            'billed': round(timesheet.billed + timesheet_temp.billed, 2),
                            'agreed': round(timesheet.agreed + timesheet_temp.agreed, 2),
                            'timesheets': [timesheet, timesheet_temp],
                        })

                    temp_billed += timesheet_temp.billed
                    temp_agreed += timesheet_temp.agreed
                    temp_timesheets_id.append(timesheet_temp)
                if len(timesheets[timesheets.index(timesheet) + 1:]) > 0:
                    result[service_code].append({
                        'billed': temp_billed,
                        'agreed': temp_agreed,
                        'timesheets': temp_timesheets_id,
                    })

        return result

    def update_pr_amount(self, timesheet_id: str, amount: str):
        self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/span[contains(@class, "edit-copay-amount")]')
        self.browser.click_element_when_visible(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/span[contains(@class, "edit-copay-amount")]')
        common.wait_element(self.browser, '//input[contains(@class, "input-sm")]')
        self.browser.input_text_when_element_is_visible('//input[contains(@class, "input-sm")]', str(amount))
        self.browser.click_element_when_visible('//button[contains(@class, "editable-submit")]')
        self.browser.wait_until_element_is_not_visible('//button[contains(@class, "editable-submit")]')

    def post_processing(self, timesheets: list, eob_for_current_date: dict) -> None:
        combined: dict = self.get_combined_timesheets(timesheets)
        is_one_updated: bool = False

        for code, amounts in eob_for_current_date.items():
            for eob in amounts:
                if code in combined:
                    for item in combined[code]:
                        if round(item['billed'], 2) == round(eob['billed'], 2):
                            common.log_message(f"{code}: Billed {eob['billed']}. Allowed rate {eob['allowed']}")

                            for timesheet in item['timesheets']:
                                if timesheet.processed:
                                    continue
                                if eob['allowed'] == eob['prov_pd']:
                                    if timesheet.pr_amount != .0:
                                        common.log_message(f'Patient responsibility is updated to 0.00 because the allowed amount is equal to the prov_pd amount. Timesheet {timesheet.timesheet_id}')
                                        self.update_pr_amount(timesheet.timesheet_id, '0')
                                    timesheet.processed = True
                                elif round(eob['allowed'] - eob['prov_pd'], 2) == round(eob['obligation_amount'], 2):
                                    if timesheet.pr_amount != eob['obligation_amount']:
                                        common.log_message(f'Patient responsibility is updated for timesheet {timesheet.timesheet_id}')
                                        self.update_pr_amount(timesheet.timesheet_id, str(eob['obligation_amount']))
                                    timesheet.processed = True
                                    is_one_updated = True
                                    break
                        if is_one_updated:
                            break
                if is_one_updated:
                    break
            if is_one_updated:
                break
        failed_timesheets: list = []
        for timesheet in timesheets:
            if not timesheet.processed:
                failed_timesheets.append(timesheet)
        if failed_timesheets:
            self.select_rows_and_apply_label(failed_timesheets, 'Unmatched PR')

    def open_window_with_insurances(self) -> None:
        common.click_and_wait(
            browser=self.browser,
            locator_for_click="//th[contains(.,'Payor')]/a/i",
            locator_for_wait="//div/span[text()='insurances']"
        )
        common.wait_element(self.browser, "//div/span[text()='insurances']/../../div/ul/li")

    def get_list_of_insurances_from_current_page(self) -> list:
        all_insurances = self.browser.find_elements("//div/span[text()='insurances']/../../div/ul/li")
        list_of_valid_insurances = []
        for insurance in all_insurances:
            insurance_name = str(insurance.text)
            if self.does_need_skip_insurance(insurance_name):
                continue
            if len(insurance_name) > 0 and not insurance_name.startswith('>'):
                list_of_valid_insurances.append(str(insurance.find_element_by_tag_name('span').get_attribute('innerHTML')))
        return list_of_valid_insurances

    def get_list_of_insurances(self) -> list:
        self.open_window_with_insurances()
        list_of_valid_insurances: list = self.get_list_of_insurances_from_current_page()

        while True:
            if self.is_click_next_clients_page('insurances'):
                temp: list = self.get_list_of_insurances_from_current_page()
                list_of_valid_insurances += temp
            else:
                break

        return list_of_valid_insurances

    def select_insurance_from_list(self, insurance_name: str) -> None:
        self.browser.reload_page()
        self.open_window_with_insurances()

        selector_for_click: str = '//a/span[text()=("' + insurance_name + '")]/..'
        selector_as_result: str = '//em[contains(.,"Insurance: ' + insurance_name.strip() + '")]'
        self.scroll_into_view_item(selector_for_click, selector_as_result, 'insurances')
        common.wait_element(self.browser, '//em[contains(.,"Insurance: ' + insurance_name.strip() + '")]')

    def get_new_timesheets_id(self) -> list:
        new_timesheets: list = []

        try:
            self.browser.click_element_when_visible('//a[text()="New "]')
            common.wait_element(self.browser, '//em[text()="Billing Status: New"]')
            if self.browser.does_page_contain_element('//div[text()="No results matched your keywords, filters, or date range" and not(@style="display: none;")]'):
                return []
            rows: list = self.browser.find_elements('//tr[contains(@id, "billing-grid-row-")]')
            for row in rows:
                new_timesheets.append(row.get_attribute('id').split('-')[-1])
        except Exception as ex:
            common.log_message('get_new_timesheets_id(): ' + str(ex))
        finally:
            self.browser.click_element_when_visible('//a[text()="Outstanding "]')
            common.wait_element(self.browser, '//em[text()="Billing Status: Outstanding"]')

        return new_timesheets

    def apply_patient_responsibility(self, input_insurance: str) -> None:
        self.apply_filter(self.filter_name, '&pageSize=750')
        if self.is_no_results('No results matched {} filter and date range'.format(self.filter_name)):
            return

        # close left side menu
        if self.browser.does_page_contain_element('//a[@data-click="closeMenu"]') and \
                self.browser.find_element('//a[@data-click="closeMenu"]').is_displayed():
            self.browser.click_element_when_visible('//a[@data-click="closeMenu"]')

        self.headers_index = self.find_header_index(
            ['client', 'date', 'payor', 'service/auth', 'agreed', 'pr amt.', 'paid', 'owed']
        )
        if not self.headers_index:
            self.browser.reload_page()
            time.sleep(5)
            self.headers_index = self.find_header_index(
                ['client', 'date', 'payor', 'service/auth', 'agreed', 'pr amt.', 'paid', 'owed']
            )

        list_of_valid_insurances = self.get_list_of_insurances()
        for insurance_name in list_of_valid_insurances:
            # START TEST
            if input_insurance.strip().lower() != insurance_name.strip().lower():
                continue
            # END TEST
            common.log_message(f'{insurance_name} processing has been started')

            self.select_insurance_from_list(insurance_name)

            common.log_message('Get a list of all clients')
            self.open_window_with_clients()
            valid_clients: list = self.get_list_of_clients()
            self.browser.reload_page()
            self.open_window_with_clients()
            common.log_message(f'{len(valid_clients)} clients were found for processing')

            for client_name in valid_clients:
                try:
                    common.log_message('=============================================================================')
                    self.open_window_with_clients()
                    client_id = self.select_client_from_list(client_name)
                    common.log_message(f'Start of client processing: {client_name} ({client_id})')
                    if self.browser.does_page_contain_element('//div[text()="No results matched your keywords, filters, or date range" and not(@style="display: none;")]'):
                        common.log_message(f'ERROR: No rows found for {client_name} client')
                        continue

                    if self.browser.does_page_contain_element('//a[@title="Close sidebar"]'):
                        if self.browser.find_element('//a[@title="Close sidebar"]').is_displayed():
                            self.browser.click_element_when_visible('//a[@title="Close sidebar"]')

                    timesheets_to_exclude: list = self.get_new_timesheets_id()

                    timesheets_by_date: dict = self.get_timesheets_for_processing()
                    for date, timesheets in timesheets_by_date.items():
                        eob_for_current_date: dict = {}
                        common.log_message('--------------------------------------------------------------------')
                        for timesheet in timesheets:
                            try:
                                if timesheet.timesheet_id in timesheets_to_exclude:
                                    timesheet.processed = True
                                    common.log_message(f'Skip New timesheet: {timesheet.timesheet_id}. Date of service: {date}')
                                    continue
                                common.log_message(f'Start of timesheet processing: { timesheet.timesheet_id }. Date of service: {date}')
                                timesheet.client_id = client_id
                                timesheet.client_name = client_name

                                columns: list = self.browser.find_elements(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td')

                                timesheet.current_payor = str(columns[self.headers_index['payor']].text)
                                if timesheet.current_payor[3:].strip().lower() not in self.mapping.payor_mapping:
                                    common.log_message('Non Insurance Payers')
                                    continue

                                timesheet.owed = float(str(columns[self.headers_index['owed']].text).replace(',', ''))
                                if timesheet.owed == 0.0:
                                    common.log_message('SUCCESS: Owed amount equal 0.0')
                                    timesheet.processed = True
                                    continue

                                if 'CO Medicaid'.lower() in timesheet.current_payor.lower() \
                                        or 'AHCCCS'.lower() in timesheet.current_payor.lower():
                                    if timesheet.owed > 0.0:
                                        self.select_rows_and_apply_label([timesheet], 'PR Owed Error')
                                    else:
                                        common.log_message(f'SUCCESS: Payor {timesheet.current_payor}')
                                    timesheet.processed = True
                                else:
                                    timesheet.set_service(str(columns[self.headers_index['service/auth']].text).strip())
                                    timesheet.billed = float(self.browser.get_text(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]/td[contains(@class, "charge") and not(contains(@data-bind,"useAgreedView()"))]').replace(',', ''))

                                    timesheet.pr_amount = float(str(columns[self.headers_index['pr amt.']].text).replace(',', ''))
                                    if round(timesheet.owed, 2) == round(timesheet.pr_amount, 2):
                                        common.log_message('SUCCESS: Patient responsibility amount equal the Owed amount')
                                        timesheet.processed = True
                                        continue

                                    timesheet.agreed = float(str(columns[self.headers_index['charges_agreed']].text).replace(',', ''))
                                    timesheet.paid = float(str(columns[self.headers_index['paid']].text).replace(',', ''))
                                    if round(timesheet.agreed, 2) == round(timesheet.paid, 2):
                                        self.update_pr_amount(timesheet.timesheet_id, '0')
                                        common.log_message('SUCCESS: Agreed amount equal the paid amount')
                                        timesheet.processed = True
                                        continue

                                    timesheet.set_date_and_time(columns[self.headers_index['date']].text)
                                    if not eob_for_current_date:
                                        eob_for_current_date: dict = self.waystar.get_eob_data(client_name, timesheet.date_of_service)
                                        if not eob_for_current_date:
                                            self.select_rows_and_apply_label(timesheets, 'Missing EOB')
                                            break
                                    timesheet.eob = eob_for_current_date
                            except Exception as timesheet_error:
                                common.log_message('Timesheet processing error: ' + str(timesheet_error), 'ERROR')
                                traceback.print_exc()
                                self.browser.capture_page_screenshot(os.path.join(
                                    os.environ.get("ROBOT_ROOT", os.getcwd()),
                                    'output',
                                    f'Something_went_wrong_Timesheet_{timesheet.timesheet_id}.png')
                                )

                                common.log_message('ERROR: {} processing failed. Something went wrong.'.format(client_name), 'ERROR')
                        if not self.is_all_processed(timesheets):
                            self.post_processing(timesheets, eob_for_current_date)
                except Exception as client_error:
                    common.log_message('Client processing error: ' + str(client_error), 'ERROR')
                    traceback.print_exc()
                    self.browser.capture_page_screenshot(os.path.join(
                        os.environ.get("ROBOT_ROOT", os.getcwd()),
                        'output',
                        'Something_went_wrong_{}.png'.format(str(client_name).replace('"', '').replace("'", "")))
                    )

                    if self.browser.does_page_contain_element("//input[@type='password']"):
                        common.log_message('ERROR: {} processing failed. An unexpected error occurred and the bot was logged out.'.format(client_name), 'ERROR')
                        self.login_to_central_reach()
                    elif 'element click intercepted' in str(client_error):
                        common.log_message('ERROR: {} processing failed. Looks like there is a new popup we need to close.'.format(client_name), 'ERROR')
                    elif 'not visible after' in str(client_error):
                        common.log_message('ERROR: {} processing failed. Looks like the required element did not appear.'.format(client_name), 'ERROR')
                    else:
                        common.log_message('ERROR: {} processing failed. Something went wrong.'.format(client_name),'ERROR')

                    self.apply_filter(self.filter_name, '&pageSize=750')
                    self.select_insurance_from_list(insurance_name)
                    self.open_window_with_clients()
