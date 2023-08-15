from RPA.Browser.Selenium import Selenium
from libraries import common
from urllib.parse import urlparse
import datetime
import time
import os
import shutil
import re


class CentralReachCore:

    def __init__(self, credentials: dict):
        self.browser: Selenium = Selenium()
        self.browser.timeout = 60
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.path_to_temp: str = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'cr')
        self.base_url: str = self.get_base_url()
        self.login_to_site()

        self.start_date: datetime = datetime.date.today().replace(day=1)
        self.end_date: datetime = datetime.date.today()

    def get_base_url(self) -> str:
        parsed_uri = urlparse(self.url)
        base_url: str = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        return base_url

    def login_to_site(self) -> None:
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
                self.wait_element('//input[@type="password"]', is_need_screen=False, timeout=10)

                self.check_scheduled_maintenance()

                self.wait_element('//input[@type="password"]', is_need_screen=False)
                self.browser.input_text_when_element_is_visible('//input[@type="text"]', self.login)
                self.browser.input_text_when_element_is_visible('//input[@type="password"]', self.password)
                self.browser.click_button_when_visible('//button[@class="btn"]')

                if self.browser.does_page_contain_element('//div[@class="loginError"]/div[text()="There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support"]'):
                    elem = self.browser.find_element('//div[@class="loginError"]/div[text()="There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support"]')
                    if elem.is_displayed():
                        common.log_message("Logging into CentralReach failed. There was an unexpected problem signing in.".format(count), 'ERROR')
                        raise Exception("There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support")

                self.wait_element_and_refresh('//span[text()="Favorites"]', is_need_screen=False)
                self.is_site_available = self.browser.does_page_contain_element('//span[text()="Favorites"]')
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

    def close_specific_windows(self, selector: str) -> None:
        try:
            if self.browser.does_page_contain_element(selector):
                elements: list = self.browser.find_elements(selector)
                for element in elements:
                    try:
                        if element.is_displayed():
                            common.log_message('A pop-up appeared and the bot closed it. Please validate the screenshot of the pop-up in the artifacts.', 'ERROR')
                            self.browser.capture_page_screenshot(
                                os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output',
                                             'Pop_up_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))
                            element.click()
                            self.browser.wait_until_element_is_not_visible('({})[{}]'.format(selector, elements.index(element) + 1))
                    except:
                        time.sleep(1)
        except:
            pass

    def check_scheduled_maintenance(self):
        if self.browser.does_page_contain_element("//p[text()='Scheduled Maintenance']"):
            if self.browser.find_element("//p[text()='Scheduled Maintenance']").is_displayed():
                common.log_message("Data processing stopped due to Scheduled Maintenance. Please run the bot again when the CR is available", 'ERROR')
                self.browser.capture_page_screenshot(
                    os.path.join(
                        os.environ.get("ROBOT_ROOT", os.getcwd()),
                        'output',
                        'Centralreach_scheduled_maintenance.png')
                )
                exit(0)

    def wait_element(self, xpath: str, timeout: int = 60, is_need_screen: bool = True) -> None:
        is_success: bool = False
        timer: datetime = datetime.datetime.now() + datetime.timedelta(0, timeout)

        while not is_success and timer > datetime.datetime.now():
            self.close_specific_windows('//button[contains(@id, "pendo-close-guide")]')
            self.close_specific_windows('//button[text()="Okay, got it!"]')
            self.close_specific_windows('//button[text()="Remind Me Later"]')
            self.close_specific_windows('//button[text()="REGISTER NOW"]')

            self.check_scheduled_maintenance()

            time.sleep(1)
            if self.browser.does_page_contain_element(xpath):
                try:
                    is_success = self.browser.find_element(xpath).is_displayed()
                except:
                    time.sleep(1)
            if not is_success:
                if self.browser.does_page_contain_element("//div[@id='select2-drop']/ul[@class='select2-results']/li[@class='select2-no-results']"):
                    elem = self.browser.find_element("//div[@id='select2-drop']/ul[@class='select2-results']/li[@class='select2-no-results']")
                    if elem.is_displayed():
                        break
        if not is_success and is_need_screen:
            common.log_message('Element \'{}\' not available'.format(xpath), 'ERROR')
            self.browser.capture_page_screenshot(
                os.path.join(os.environ.get(
                    "ROBOT_ROOT", os.getcwd()),
                    'output',
                    'Element_not_available_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
                )
            )

    def wait_element_and_refresh(self, locator: str, timeout: int = 120, is_need_screen: bool = True) -> None:
        timer: datetime = datetime.datetime.now() + datetime.timedelta(0, timeout)
        is_success: bool = False

        while not is_success and timer > datetime.datetime.now():
            self.wait_element(locator, 45, False)
            if self.browser.does_page_contain_element(locator):
                try:
                    is_success = self.browser.find_element(locator).is_displayed()
                    if not is_success:
                        self.browser.reload_page()
                except Exception as ex:
                    print(str(ex))
                    self.browser.reload_page()
                    time.sleep(1)
            else:
                self.browser.reload_page()
        if not is_success and is_need_screen:
            common.log_message('Element "{}" not available'.format(locator), 'ERROR')
            self.browser.capture_page_screenshot(
                os.path.join(
                    os.environ.get("ROBOT_ROOT", os.getcwd()),
                    'output',
                    'Element_not_available_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
                )
            )

    def wait_and_click(self, xpath: str, timeout: int = 60) -> None:
        self.wait_element(xpath, timeout)
        self.browser.scroll_element_into_view(xpath)
        self.browser.click_element_when_visible(xpath)

    def apply_filter(self, filter_name: str, additional_params: str = ''):
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
        if additional_params:
            updated_url: str = self.browser.get_location()
            updated_url += additional_params
            self.browser.go_to(updated_url)

        self.browser.wait_until_element_is_not_visible("//em[contains(., '<loading>')]", datetime.timedelta(seconds=45))
        self.browser.wait_until_element_is_not_visible("//div[contains(@data-bind, 'loading()')]", datetime.timedelta(seconds=45))

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
            if message:
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

    def select_rows_and_apply_label(self, timesheets: list, label_add: str, label_remove: str = '') -> None:
        if not label_remove:
            timesheets_id: list = [timesheet.timesheet_id for timesheet in timesheets]
            common.log_message(f'ERROR: Label "{label_add}" applied to timesheet { ", ".join(timesheets_id) }')
            for timesheet in timesheets:
                timesheet.processed = True

        self.select_rows(timesheets)
        self.apply_label(label_add, label_remove)
        self.unselect_rows(timesheets)

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
