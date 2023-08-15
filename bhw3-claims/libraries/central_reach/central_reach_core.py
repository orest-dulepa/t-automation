import re

from RPA.Browser.Selenium import Selenium
from urllib.parse import urlparse
import shutil

import datetime
import os
import time

from selenium.webdriver.common.keys import Keys
import dateutil.parser
from libraries import common
from libraries.central_reach.central_reach_utils.central_reach_requests import CentralReachRequests
from libraries.models.bulk_claim_model import BulkClaimModel
from libraries.models.client_model import ClientModel
from libraries.models.payor_model import PayorModel
from libraries.models.timesheet_model import TimesheetModel


class CentralReachCore:

    def __init__(self, credentials: dict, input_data):
        self.browser: Selenium = Selenium()
        self.browser.timeout = 60
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.path_to_temp: str = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'cr')
        self.base_url: str = self.get_base_url()

        self.start_date: datetime = datetime.datetime.strptime(input_data[0], "%m/%d/%Y")
        self.end_date: datetime = datetime.datetime.strptime(input_data[1], "%m/%d/%Y")

        self.requests_obj = CentralReachRequests(credentials)
        self.billing_table_headers: list = [
            "time",
            "date",
            "client",
            "service/auth"
        ]
        self.header_indexs = dict()
        self.claims_bot_filter = self.requests_obj.get_filter_by_name("Claims Bot")
        self.filter_tricare_audit = self.requests_obj.get_filter_by_name("Tricare Audit")
        self.label_items = self.requests_obj.get_labels()

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
            self.wait_element(locator, 30, False)
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

    def go_to_by_link(self, link_url: str):
        self.browser.go_to(link_url)

    def take_screenshot(self, screen_name: str = 'screenshot', folder_path: str = '') -> str:
        screen_name.replace(" ", "_")
        if not folder_path:
            folder_path = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output')

        full_screen_name: str = f"{screen_name}_{datetime.datetime.now().strftime('%H_%M_%S')}.png"
        path_to_screen = os.path.join(folder_path, full_screen_name)
        self.browser.capture_page_screenshot(path_to_screen)
        return path_to_screen

    def wait_element_exist(self, xpath: str, timeout: int = 60) -> None:
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
                if self.browser.does_page_contain_element(
                        "//div[@id='select2-drop']/ul[@class='select2-results']/li[@class='select2-no-results']"):
                    elem = self.browser.find_element(
                        "//div[@id='select2-drop']/ul[@class='select2-results']/li[@class='select2-no-results']")
                    if elem.is_displayed():
                        break
        if not is_success:
            raise Exception(f'Element \'{xpath}\' not available. ')

    def wait_and_click_is_exist(self, xpath: str, timeout: int = 60) -> None:
        self.wait_element_exist(xpath, timeout)
        self.browser.scroll_element_into_view(xpath)
        self.browser.click_element_when_visible(xpath)

    def is_element_exist(self, xpath: str, timeout: int = 60) -> bool:
        try:
            self.wait_element_exist(xpath, timeout)
            return True
        except:
            return False

    def is_location_valid(self, acceptable_locations, location_from_page) -> bool:
        for acceptable_location in acceptable_locations:
            if acceptable_location.replace(" ", "").lower() in location_from_page.replace(" ", "").lower():
                return True
        return False

    def get_timesheets(self):
        return self.browser.find_elements('//table/tbody/tr[contains(@id, "billing-grid-row-")]')

    def get_timesheets_data(self) -> [list]:
        timesheet_elems = self.get_timesheets()
        self.header_indexs = self.find_header_index(
            required_headers=self.billing_table_headers,
            header_selector='//thead/tr[@class="white"][th[text() = "Time"]/following-sibling::th[div/a[text()="Service/Auth"]]]',
            plus_int=1
        )

        timesheet_data = list(map(lambda x: self.__convert_elem_to_timesheet_model__(x), timesheet_elems))
        return timesheet_data

    def __convert_elem_to_timesheet_model__(self, elem):
        timesheet_model = TimesheetModel()
        id = self.browser.get_element_attribute(elem, 'id').replace("billing-grid-row-", "")
        timesheet_model.id = id
        timesheet_model.time_str = self.browser.find_element(
            f'//table/tbody/tr[contains(@id, "billing-grid-row-{id}")]/td[{self.header_indexs["time"]}]/span').text.strip()
        timesheet_model.client_id = self.browser.get_element_attribute(self.browser.find_element(
            f'//table/tbody/tr[contains(@id, "billing-grid-row-{id}")]/td[{self.header_indexs["client"]}]/a[@contactid]'),
                                                                       'contactid').strip()
        timesheet_model.service_auth = self.browser.find_element(
            f'//table/tbody/tr[contains(@id, "billing-grid-row-{id}")]/td[{self.header_indexs["service/auth"]}]').text.strip()
        return timesheet_model

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
                self.wait_element_exist(expected_locator)
                self.browser.reload_page()
                is_success = True
            except Exception as ex:
                time.sleep(3)
                exception = ex
                count += 1

        if is_success is False:
            print("Error-Retry scope.The element was not appeared." + str(exception))
            raise exception

    def get_timesheets_by_filter_using_requests(self, addition_filter: dict = None):
        filter_page: dict = dict()
        filter_page.update(self.claims_bot_filter)
        if addition_filter is not None:
            filter_page.update(addition_filter)

        items = self.requests_obj.get_billings(start_date=self.start_date, end_date=self.end_date,
                                               page_filter=filter_page)
        timesheets_data = list(map(lambda x: self.__convert_request_items_to_timesheet_model__(x), items))
        return timesheets_data

    def __convert_request_items_to_timesheet_model__(self, item):
        timesheet_model = TimesheetModel()
        timesheet_model.id = item["Id"]
        timesheet_model.time_str = f'{item["DateTimeFrom"]} - {item["DateTimeTo"]}'
        timesheet_model.time_from = dateutil.parser.parse(item["DateTimeFrom"])
        timesheet_model.time_to = dateutil.parser.parse(item["DateTimeTo"])
        timesheet_model.date = dateutil.parser.parse(item["DateTimeTo"]).date()
        timesheet_model.client_id = item["ClientId"]
        timesheet_model.client = ClientModel()
        timesheet_model.client.id = item["ClientId"]
        timesheet_model.client.first_name = item["ClientFirstName"]
        timesheet_model.client.last_name = item["ClientLastName"]
        timesheet_model.service_auth = item["ProcedureCodeString"]
        timesheet_model.procedure_code_id = item["ProcedureCodeId"]
        timesheet_model.provider_id = item["ProviderId"]
        timesheet_model.location = item["Location"]
        timesheet_model.amount_owed = item["AmountOwed"]
        timesheet_model.units_of_service = item["UnitsOfService"]
        timesheet_model.time_worked_in_mins = item["TimeWorkedInMins"]
        return timesheet_model

    def get_all_payors_from_init_billing_page(self):
        page_filter: dict = dict()
        page_filter.update(self.claims_bot_filter)
        payors = self.requests_obj.get_payors_of_billing_page(start_date=self.start_date, end_date=self.end_date,
                                                              page_filter=page_filter)
        return payors

    def get_billing_timesheets_by_payor_id(self, payor_id: str, addition_filter: dict = None):
        filter_page: dict = {"insuranceId": payor_id}
        if addition_filter is not None:
            filter_page.update(addition_filter)
        return self.get_timesheets_by_filter_using_requests(filter_page)

    def __convert_request_item_to_payor_model__(self, item):
        payor = PayorModel()
        payor.id = item['id']
        payor.name = item['parentName']
        return payor

    def get_all_payors_data(self):
        payors_list = list()
        for item in self.get_all_payors_from_init_billing_page():
            payor = self.__convert_request_item_to_payor_model__(item)
            payors_list.append(payor)

        return payors_list

    def click_checkbox_to_select_clients(self, attempts: int = 3, timeout: int = 5):
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

    def select_checkbox_of_timesheet_by_id(self, timesheet_id):
        unselected_xpath = f'//*[@id="content"]/table/tbody/tr[@id="billing-grid-row-{timesheet_id}" and not (contains(@class, "selected"))]'
        attempts: int = 3
        timeout: int = 5
        is_success = False
        count = 0
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                if self.browser.is_element_visible(unselected_xpath):
                    self.browser.scroll_element_into_view(unselected_xpath + "/td/input[@class='select-entry']")
                    self.browser.click_element_when_visible(
                        unselected_xpath + "/td/input[@class='select-entry']")

                selected_xpath = unselected_xpath.replace("not","")
                self.wait_element_exist(selected_xpath)
                is_success=True
            except Exception as ex:
                time.sleep(timeout)
                exception = Exception("Unable to select timesheet by id: "+ timesheet_id + " .Reason: "+str(ex))
                count += 1

        if is_success is False:
            print(str(exception))


    def add_labels(self, label_values: list):
        is_success = False
        count = 0
        attempts = 4
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                self.browser.wait_and_click_button('//button[contains(., "Label selected")]')
                self.wait_element_exist('//h2[text() = "Bulk Apply Labels"]')

                for label_value in label_values:
                    self.browser.input_text_when_element_is_visible('//*[@id="s2id_autogen4"]', label_value)
                    time.sleep(1)
                    self.wait_element_exist(f'//*[@id="select2-drop"]/ul/li/div[contains(., "{label_value}")]')

                    self.browser.click_element_when_visible(
                        f'//*[@id="select2-drop"]/ul/li/div[text()="{label_value}"]')
                    self.wait_element_exist(f'//*[@id="s2id_autogen3"]/ul[li/div[contains(., "{label_value}")]]')

                self.browser.click_element_when_visible('//button[contains(.,"Apply Label Changes")]')
                self.browser.wait_until_page_does_not_contain('//h2[text() = "Bulk Apply Labels"]')
                is_success = True
            except Exception as ex:
                self.browser.wait_and_click_button('//button[contains(.,"Apply Label Changes")]/following-sibling::button[text()="Close"]')
                self.browser.wait_until_page_does_not_contain('//h2[text() = "Bulk Apply Labels"]')
                time.sleep(3)
                exception = Exception("Add label. " + str(ex))
                count += 1

        if is_success is False:
            raise exception

    def input_value(self, elem_for_input, value, is_click_enter=True, attempts=3, timeout=1):
        is_success = False
        count = 0
        exception: Exception = Exception()
        while (count < attempts) and (is_success is False):
            try:
                self.browser.input_text_when_element_is_visible(elem_for_input, value)
                time.sleep(timeout)
                if is_click_enter:
                    elem_for_input.send_keys(Keys.ENTER)

                if value in self.browser.get_element_attribute(
                        self.browser.find_elements(elem_for_input),
                        "value"):
                    is_success = True
                else:
                    raise Exception("Modifier didn't input")

            except Exception as ex:
                time.sleep(3)
                exception = ex
                count += 1

        if is_success is False:
            print("Error-Retry scope.The element was not appeared." + str(exception))
            raise exception

    def get_bulk_claims_by_filter(self, filter_page):
        items = self.requests_obj.get_payor_bulk_claims(start_date=self.start_date, end_date=self.end_date,
                                               page_filter=filter_page)
        claims_data = list(map(lambda x: self.__convert_request_items_to_bulk_claim_model__(x), items))
        return claims_data

    def __convert_request_items_to_bulk_claim_model__(self, item_bulk_claim) -> BulkClaimModel:
        bulk_claim = BulkClaimModel()
        bulk_claim.client_name = item_bulk_claim["ClientName"]

        bulk_claim.codes = list()
        for item in re.findall(r"\WCode\d+", str.join(";", item_bulk_claim)):
            item = item.replace(";","")
            if len(item_bulk_claim[item]) >0:
                bulk_claim.codes.append(item_bulk_claim[item])

        bulk_claim.diag_pointers = list()
        for item in re.findall(r"\WdiagPointer\d+", str.join(";", item_bulk_claim)):
            item = item.replace(";", "")
            if len(item_bulk_claim[item]) > 0:
                bulk_claim.diag_pointers.append(item_bulk_claim[item])

        return bulk_claim

    def open_and_get_new_tab(self, link_url):
        self.browser.execute_javascript("window.open('" + link_url + "');")
        browser_tabs = self.browser.get_window_handles()
        return browser_tabs[len(browser_tabs) - 1]

    def close_tab_and_back_to_previous(self):
        browser_tabs = self.browser.get_window_handles()
        self.browser.close_window()
        self.browser.switch_window(browser_tabs[len(browser_tabs)-2])

    def is_browser_opened(self) -> bool:
        try:
            title = self.browser.driver.title
            return True
        except Exception as ex:
            return False



