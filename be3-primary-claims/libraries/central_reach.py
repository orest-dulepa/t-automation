from RPA.PDF import PDF
from RPA.Browser.Selenium import Selenium
from libraries import common
from urllib.parse import urlparse
import os
import re
import time
import datetime
from libraries.timesheet import Timesheet

pdf_reader = PDF()


def click_element(browser: Selenium, locator: str):
    common.wait_element(
        browser=browser,
        selector=locator
    )
    is_clicked = False
    try_count = 0
    while not is_clicked and try_count < 3:
        try_count += 1
        try:
            browser.click_element(locator=locator)
            is_clicked = True
        except Exception as ex:
            common.log_message(str(ex), 'TRACE')


def click_bunch_of_elements(browser: Selenium, paths: list):
    for locator in paths:
        click_element(
            browser=browser,
            locator=locator
        )


class CentralReach:
    filter_overlap_check = 'Overlap Check'
    filter_duplicate_check = 'Duplicate Check'
    filter_no_claims = 'No claims'

    assign_task_to = 'Jake Downs'

    list_of_payor_for_skip = [
        'the BHPN',
        'Tufts',
        'Tufts Health Public Plans',
        'Blue Shield of California',
        'Blue Cross Blue Shield of North Carolina',
        'CalOptima',
        'Allied Health',
        'Valley Mountain Regional Center',
    ]

    def __init__(self, credentials):
        self.browser: Selenium = Selenium()
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.login_to_central_reach()
        self.base_url: str = self.get_base_url()
        self.client_id: str = ''
        self.start_date: datetime = datetime.datetime.now() - datetime.timedelta(days=187)
        self.end_date: datetime = datetime.datetime.now() - datetime.timedelta(days=7)

    def get_base_url(self) -> str:
        parsed_uri = urlparse(self.url)
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

    def login_to_central_reach(self) -> None:
        self.browser.close_browser()
        self.is_site_available = False
        self.browser.timeout = 45
        preferences = {
            'download.default_directory': os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'pdf'),
            'plugins.always_open_pdf_externally': True,
            'download.directory_upgrade': True,
            'download.prompt_for_download': False,
            'dom.ipc.plugins.enabled.libflashplayer.so': False,
            'timeouts': {'pageLoad': 30},
        }

        count: int = 0
        while count <= 3 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.url, preferences=preferences)
                self.browser.set_window_size(1920, 1080)
                self.browser.maximize_browser_window()
                common.wait_element(self.browser, "//input[@type='password']", is_need_screen=False, timeout=10)
                if self.browser.does_page_contain_element("//p[text()='Scheduled Maintenance']"):
                    elem = self.browser.find_element("//p[text()='Scheduled Maintenance']")
                    if elem.is_displayed():
                        common.log_message("Logging into CentralReach failed. Scheduled Maintenance.",
                                           'ERROR')
                        self.browser.capture_page_screenshot(
                            os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()),
                                         'output',
                                         'Centralreach_scheduled_maintenance.png'))
                        return
                common.wait_element(self.browser, "//input[@type='password']", is_need_screen=False)
                self.browser.input_text_when_element_is_visible("//input[@type='text']", self.login)
                self.browser.input_text_when_element_is_visible("//input[@type='password']", self.password)
                self.browser.click_element_when_visible("//button[@class='btn']")
                common.wait_element_and_refresh(self.browser, "//span[text()='Favorites']", is_need_screen=False)
                self.is_site_available = self.browser.does_page_contain_element("//span[text()='Favorites']")
            except Exception as ex:
                print(str(ex))
                common.log_message("Logging into CentralReach. Attempt #{} failed".format(count), 'ERROR')
                self.browser.capture_page_screenshot(os.path.join(os.environ.get(
                    "ROBOT_ROOT", os.getcwd()),
                    'output',
                    'Centralreach_login_failed_{}.png'.format(count))
                )
                self.browser.close_browser()
            finally:
                count += 1

    def apply_filter(self, filter_name: str, additional_params: str = '') -> None:
        # Go to billing page
        common.wait_element(self.browser, "//th[contains(.,'Payor')]/a/i")
        old_url: str = self.browser.get_location()

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
        updated_url: str = self.browser.get_location()
        if old_url == updated_url:
            time.sleep(1)
            updated_url: str = self.browser.get_location()
        updated_url += additional_params

        # Sometimes it doesn't work properly
        self.browser.go_to(updated_url)
        self.browser.go_to(updated_url)
        self.browser.go_to(updated_url)

        self.browser.wait_until_element_is_not_visible("//em[text()='Overlapping: <loading>']", 60)

    def find_header_index(self, required_headers: list) -> dict:
        headers_index: dict = {}
        find_headers: list = self.browser.find_elements("//thead/tr[@class='white']")

        for row in find_headers:
            count: int = 0
            for header in required_headers:
                if header.lower() in row.text.lower():
                    count += 1
            if count == len(required_headers):
                headers_columns: list = row.find_elements_by_tag_name("th")
                for column_name in headers_columns:
                    tmp_column_name: str = str(column_name.text).strip().lower()
                    if tmp_column_name in required_headers and tmp_column_name not in headers_index:
                        headers_index[tmp_column_name] = headers_columns.index(column_name)
                    if tmp_column_name == 'agreed' and tmp_column_name in headers_index:
                        headers_index['charges_agreed'] = headers_columns.index(column_name)
                    try:
                        if not tmp_column_name:
                            column_name.find_element_by_class_name('fa-tasks')
                            headers_index['tasks'] = headers_columns.index(column_name)
                    except:
                        pass
                    try:
                        if not tmp_column_name:
                            column_name.find_element_by_class_name('fa-file')
                            headers_index['file'] = headers_columns.index(column_name)
                    except:
                        pass
                break
        return headers_index

    def assign_task_form(self, assign_task_to: str, task_name: str, task_description: str = '') -> None:
        click_bunch_of_elements(
            browser=self.browser,
            paths=[
                '//a[@class="btn btn-default dropdown-toggle"]',
                '//a[@data-bind="click: listVm.addTaskForBillingEntries"]',
            ]
        )
        # filling assign task form
        self.browser.input_text_when_element_is_visible(
            locator='//input[@placeholder="Name of new task"]',
            text=task_name
        )
        click_element(
            browser=self.browser,
            locator='//div[@class="col-sm-6"]/select/option[@value="1"]'
        )
        click_element(
            browser=self.browser,
            locator='//div[@class="select2-search"]/input[@placeholder="Select a person or a label"]'
        )
        self.browser.input_text_when_element_is_visible(
            locator='//div[@class="select2-search"]/input[@placeholder="Please enter 3 more characters..."]',
            text=assign_task_to
        )
        list_locator = '//div[@class="form-group"]//li[@class="select2-result select2-result-selectable select2-highlighted"]'
        common.wait_element(
            browser=self.browser,
            selector=list_locator
        )
        if (self.browser.does_page_contain_element(
                locator=list_locator
        )):
            keys = (False, 'RETURN')
            self.browser.press_keys(*keys)

        self.browser.click_element_when_visible('//button[@id="btn-create-task"]')
        self.browser.wait_until_element_is_not_visible('//button[@id="btn-create-task"]')

    def is_no_results(self) -> bool:
        common.wait_element(self.browser, '//div[@id="content"]')

        common.wait_element(
            self.browser,
            '//div[text()="No results matched your keywords, filters, or date range" and not(@style="display: none;")]',
            timeout=3,
            is_need_screen=False
        )
        if self.browser.does_page_contain_element('//div[text()="No results matched your keywords, filters, or date range" and not(@style="display: none;")]'):
            return True
        common.wait_element(self.browser, '//input[@data-bind="checked: listVm.allSelected"]')
        return False

    def find_duplicates(self) -> None:
        self.browser.go_to(self.base_url + '#billingmanager/billing/')
        self.apply_filter(self.filter_duplicate_check, '&pageSize=250')
        if self.is_no_results():
            common.log_message('There are no duplicates')
            return

        list_of_providers: list = self.get_list_of_providers()
        headers_index: dict = self.find_header_index(['client', 'date', 'time', 'payor', 'providers'])

        for provider in list_of_providers:
            common.log_message('Check duplicate for {}'.format(provider))
            try:
                self.select_provider_from_list(provider, list_of_providers)

                rows: list = self.browser.find_elements("//tbody/tr[contains(@class, 'row-item entry')]")
                count_of_rows_with_tasks: int = 0
                for row in rows:
                    columns: list = row.find_elements_by_tag_name('td')
                    if str(columns[headers_index['tasks']].text).strip():
                        count_of_rows_with_tasks += 1
                if count_of_rows_with_tasks == len(rows):
                    common.log_message('All timesheets have tasks. Timesheets are skipped')
                    continue

                self.browser.select_checkbox('//input[@data-bind="checked: listVm.allSelected"]')
                common.log_message('Duplicate detected. Creating a task')
                self.assign_task_form(self.assign_task_to, 'Review duplicates TS')
            except Exception as ex:
                common.log_message(str(ex), 'ERROR')
                self.browser.capture_page_screenshot(
                    os.path.join(
                        os.environ.get('ROBOT_ROOT', os.getcwd()),
                        'output',
                        'Something_went_wrong_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
                    )
                )

    def select_provider_from_list(self, provider: str, list_of_providers: list) -> None:
        common.click_and_wait(
            browser=self.browser,
            locator_for_click="//th/div/a[contains(.,'Providers')]/../../a/i",
            locator_for_wait="//div/span[text()='providers']"
        )
        for provider_temp in list_of_providers:
            try:
                common.wait_element(
                    browser=self.browser,
                    selector='//a/span[text()=("' + provider_temp + '")]/..',
                    timeout=5,
                    is_need_screen=False
                )
                if self.browser.does_page_contain_element('//a/span[text()=("' + provider_temp + '")]/..'):
                    self.browser.scroll_element_into_view('//a/span[text()=("' + provider_temp + '")]/..')
            except Exception as ex:
                common.log_message('Scroll into view error: ' + str(ex), 'TRACE')
            finally:
                if provider == provider_temp:
                    break
        self.browser.click_element_when_visible('//a/span[text()=("' + provider + '")]/..')
        common.wait_element(self.browser, '//em[contains(.,"Provider: ' + provider.strip() + '")]')

    def get_list_of_providers(self) -> list:
        common.click_and_wait(
            browser=self.browser,
            locator_for_click="//th/div/a[contains(.,'Providers')]/../../a/i",
            locator_for_wait="//div/span[text()='providers']"
        )

        common.wait_element(self.browser, "//div/span[text()='providers']/../../div/ul/li")
        all_providers: list = self.browser.find_elements("//div/span[text()='providers']/../../div/ul/li")

        list_of_providers: list = []
        for provider in all_providers:
            provider_name: str = str(provider.text).strip()
            if provider_name:
                list_of_providers.append(provider_name)
        return list_of_providers

    def overlap_check_by_time(self) -> None:
        list_of_providers: list = self.get_list_of_providers()
        headers_index: dict = self.find_header_index(['client', 'date', 'time', 'payor', 'providers'])

        for provider in list_of_providers:
            common.log_message('Check overlaps for {}'.format(provider))
            try:
                self.select_provider_from_list(provider, list_of_providers)

                list_of_timesheets: list = []
                payor_from_web_origin: str = ''
                rows: list = self.browser.find_elements("//tbody/tr[contains(@class, 'row-item entry')]")
                for row in rows:
                    columns: list = row.find_elements_by_tag_name('td')

                    # Check if need skip payor
                    payor_from_web_origin: str = str(columns[headers_index['payor']].text)[3:].strip()
                    payor_from_web: str = payor_from_web_origin.lower()
                    is_need_skip: bool = False
                    for payor in self.list_of_payor_for_skip:
                        if payor.lower() in payor_from_web:
                            is_need_skip = True
                            break
                    if is_need_skip:
                        list_of_timesheets.append(None)
                        continue

                    columns_value: dict = {}
                    for header, index in headers_index.items():
                        if header not in columns_value:
                            columns_value[header] = str(columns[index].text).strip()

                    timesheet: Timesheet = Timesheet(
                        columns_value['client'],
                        columns_value['date'],
                        columns_value['time'],
                        columns_value['payor'],
                        columns_value['providers'],
                        columns_value['tasks']
                    )
                    list_of_timesheets.append(timesheet)

                # Validate overlap
                for i in range(len(list_of_timesheets)):
                    for n in range(i + 1, len(list_of_timesheets)):
                        if not list_of_timesheets[i] or not list_of_timesheets[n]:
                            continue
                        if list_of_timesheets[i].check_overlap(list_of_timesheets[n]):
                            list_of_timesheets[i].is_need_check = True
                            list_of_timesheets[n].is_need_check = True

                # Check rows on web
                count_of_ts_selected: int = 0
                count_of_ts_with_task: int = 0
                count_of_ts_not_none: int = 0
                for timesheet in list_of_timesheets:
                    if timesheet:
                        count_of_ts_not_none += 1
                        if timesheet.tasks:
                            count_of_ts_with_task += 1
                        if timesheet.is_need_check:
                            count_of_ts_selected += 1
                            self.browser.scroll_element_into_view('(//input[@class="select-entry"])[{}]'.format(
                                list_of_timesheets.index(timesheet) + 1)
                            )
                            self.browser.select_checkbox('(//input[@class="select-entry"])[{}]'.format(
                                list_of_timesheets.index(timesheet) + 1)
                            )
                if count_of_ts_not_none == 0:
                    common.log_message('All timesheets have "{}" payor. Timesheets are skipped'.format(payor_from_web_origin))
                    continue
                elif not count_of_ts_selected:
                    common.log_message('There are no overlaps by time')
                    continue
                elif count_of_ts_with_task == count_of_ts_selected:
                    common.log_message('All timesheets have tasks. Timesheets are skipped')
                    continue

                common.log_message('Overlap detected. Creating a task')
                self.assign_task_form(self.assign_task_to, 'Review Overlapping TS')
            except Exception as ex:
                common.log_message(str(ex), 'ERROR')
                self.browser.capture_page_screenshot(
                    os.path.join(
                        os.environ.get('ROBOT_ROOT', os.getcwd()),
                        'output',
                        'Something_went_wrong_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
                    )
                )

    def overlap_check_by_provider(self) -> None:
        self.browser.go_to(self.base_url + '#billingmanager/billing/')
        self.apply_filter(self.filter_overlap_check, '&pageSize=750')
        if self.is_no_results():
            common.log_message('There are no overlaps by Provider')
            return
        self.overlap_check_by_time()

    def go_to_filtered_page(self):
        # Apply filter
        self.browser.go_to(self.base_url + '#billingmanager/billing/?startdate={}&enddate={}'.format(
            self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d')))

        self.apply_filter(self.filter_no_claims, f'&pageSize=750&clientId={self.client_id}')
        common.wait_element_and_refresh(self.browser, f'//em[contains(., "ID: {self.client_id}")]')
        if not self.browser.does_page_contain_element(f'//em[contains(., "ID: {self.client_id}")]'):
            common.log_message('Unable to apply filter')
            exit(1)

        if self.is_no_results():
            common.log_message('There are no timesheets for these filters')
            exit(0)

    def apply_filter_to_claims(self):
        self.go_to_filtered_page()

        headers_index: dict = self.find_header_index(['client', 'date', 'time', 'payor', 'providers', 'service/auth'])
        rows: list = self.browser.find_elements("//tbody/tr[contains(@class, 'row-item entry')]")
        list_of_valid_rows: list = []
        for row in rows:
            columns: list = row.find_elements_by_tag_name('td')
            if str(columns[headers_index['tasks']].text).strip():
                continue
            service_name: str = str(columns[headers_index['service/auth']].text).strip()
            if '97153' not in service_name and '97155' not in service_name:
                continue
            list_of_valid_rows.append(rows.index(row))

        if len(list_of_valid_rows) == 0:
            common.log_message('There are no relevant timesheets for these filters')
            exit(0)

    def open_new_tab(self):
        self.browser.execute_javascript("window.open('{}')".format(self.base_url))
        windows = self.browser.get_window_handles()
        self.browser.switch_window(windows[1])
        self.browser.set_window_size(1920, 1080)
        windows = self.browser.get_window_handles()
        self.browser.switch_window(windows[0])

    def download_and_validate_pdf(self, link_to_pdf: str, location_from_web: str, time_from_web: str) -> (bool, bool):
        is_location_match = False
        is_time_match = False

        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])
        billing_entry_id = re.search(r'billingEntryId=(\d+)', link_to_pdf)[1]
        self.browser.go_to('{}#resources/?billingEntryId={}'.format(self.base_url, billing_entry_id))

        path_to_temp = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'pdf')
        temp_files = [f for f in os.listdir(path_to_temp) if os.path.isfile(os.path.join(path_to_temp, f))]
        for file in temp_files:
            try:
                os.remove(file)
            except Exception as ex:
                common.log_message(str(ex), 'ERROR')

        common.wait_element_and_refresh(self.browser, '//em[text()="Billing Entry: {}"]'.format(billing_entry_id), 60 * 3)
        if not self.browser.does_page_contain_element('//em[text()="Billing Entry: {}"]'.format(billing_entry_id)):
            common.log_message(self.browser.get_location())
            common.log_message('Unable to get pdf document')
            self.browser.capture_page_screenshot(os.path.join(os.environ.get(
                "ROBOT_ROOT", os.getcwd()),
                'output',
                'Centralreach-unable-to-get-pdf-{}.png'.format(datetime.datetime.now().strftime('%H-%m-%S-%f')))
            )
            self.browser.go_to(self.base_url)
            self.browser.switch_window(browser_tabs[0])
            return False, False

        check_result = 'Unable to download pdf file'
        common.wait_element(self.browser, '//div[@class="ag-body-container"]/div[@role="row"]')
        rows: list = self.browser.find_elements('//div[@class="ag-body-container"]/div[@role="row"]')
        for i in range(len(rows)):
            if self.browser.does_page_contain_element('//span[text()="Files"]'):
                if self.browser.find_element('//span[text()="Files"]').is_displayed():
                    self.browser.click_element_when_visible('//span[text()="Files"]')
            common.wait_element_and_refresh(self.browser, f'//div[@row-index="{i}"]/div/span/i[contains(@class, "file")]')
            buttons = self.browser.get_element_attribute(
                locator=f'//div[@row-index="{i}"]/div/span/i[contains(@class, "file")]',
                attribute='class'
            )
            if 'pdf' in str(buttons).lower():
                click_bunch_of_elements(
                    browser=self.browser,
                    paths=[
                        f'//div[@row-index="{i}"]/div/div/a',
                        '//button[@data-click="getDownloadUrl"]',
                        '//a[contains(@data-bind,"downloadedUrl")]',
                    ]
                )
                try:
                    path_to_pdf: str = common.get_downloaded_file_path(
                        path_to_temp=os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'pdf'),
                        extension='pdf',
                        error_message='Unable to download pdf file'
                    )
                except Exception as ex:
                    print(str(ex))
                    self.browser.capture_page_screenshot(os.path.join(os.environ.get(
                        "ROBOT_ROOT", os.getcwd()),
                        'output',
                        'Centralreach-unable-to-get-pdf-{}.png'.format(datetime.datetime.now().strftime('%H-%m-%S-%f')))
                    )
                    self.browser.go_to(self.base_url)
                    self.browser.switch_window(browser_tabs[0])
                    return False, False

                check_result = common.pdf_location_timing_check(pdf_reader, path_to_pdf)
                os.remove(path_to_pdf)
                if type(check_result) == tuple:
                    break

        self.browser.go_to(self.base_url)
        self.browser.switch_window(browser_tabs[0])

        if type(check_result) == str:
            common.log_message(check_result)
            return False, False

        if type(check_result) == tuple:
            check_location, check_times, check_date = check_result

            is_location_match = str(check_location).strip().lower() == location_from_web.strip().lower()
            times_from_pdf = common.pdf_times_process(check_times)
            is_time_match = common.compare_times_cr_pdf(time_from_web, times_from_pdf)
        return is_location_match, is_time_match

    def is_need_task(self,
                     auth_number: str,
                     is_date_match: bool,
                     is_location_match: bool,
                     is_time_match: bool,
                     is_auth_code_valid: bool,
                     timesheet_id: str) -> bool:
        if auth_number and is_date_match and is_location_match and is_time_match and is_auth_code_valid:
            return False
        self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/input')
        self.browser.select_checkbox(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/input')

        if not auth_number:
            common.log_message('Reporting authorization discrepancies')
            self.assign_task_form(self.assign_task_to, 'Authorization Report')
        if not is_date_match:
            common.log_message('Reporting date discrepancies')
            self.assign_task_form(self.assign_task_to, 'Date Report')
        if not is_location_match:
            common.log_message('Reporting location discrepancies')
            self.assign_task_form(self.assign_task_to, 'Location Report')
        if not is_time_match:
            common.log_message('Reporting time discrepancies')
            self.assign_task_form(self.assign_task_to, 'Time Report')
        if not is_auth_code_valid:
            common.log_message('Reporting authorization code discrepancies')
            self.assign_task_form(self.assign_task_to, 'Authorization code Report')
        # self.assign_task_form(self.assign_task_to, 'Review Claim Errors', '')
        self.browser.unselect_checkbox(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/input')
        return True

    def generate_claim(self):
        common.log_message('Generating Claims')
        payor, list_of_claims_url = self.generating_claims()

        list_of_claims_id: list = []
        for claim_url in list_of_claims_url:
            claim_id = re.findall(r'claimId=(\d+)', claim_url)[0]
            list_of_claims_id.append(claim_id)
            common.log_message('Claim #{}'.format(claim_id), 'INFO')

            windows = self.browser.get_window_handles()
            self.browser.switch_window(windows[1])
            self.browser.go_to(f'https://members.centralreach.com/#claims/editor/?claimId={claim_id}')
            common.wait_element(self.browser, '//button[contains(., "Save Claim")]')

            list_of_errors: list = []
            list_of_errors += self.disposition_provider()
            list_of_errors += self.disposition_facility(payor)
            list_of_errors += self.disposition_patient()
            list_of_errors += self.disposition_auth()
            self.save_claim()
            common.log_message('Generating Claims Complete')

            self.browser.go_to('https://members.centralreach.com/#claims/list/?folderId=0&claimId={}'.format(claim_id))
            common.wait_element(self.browser, '//div/a[contains(., "Inbox")]')

            if self.browser.does_page_contain_element('//*[@id="claims-list-sub-module"]/div[4]/nav/div[1]/a'):
                if self.browser.find_element('//*[@id="claims-list-sub-module"]/div[4]/nav/div[1]/a').is_displayed():
                    self.browser.click_element_when_visible('//*[@id="claims-list-sub-module"]/div[4]/nav/div[1]/a')

            common.wait_element(self.browser, '//tbody[@class="claims-list"]/tr[1]/td[1]/label')
            self.browser.click_element_when_visible('//tbody[@class="claims-list"]/tr[1]/td[1]/label')

            if list_of_errors:
                common.log_message('The claim #{} has the following errors: {}'.format(claim_id, ', '.join(list_of_errors)))
                self.assign_task_claims(self.assign_task_to, ', '.join(list_of_errors))
                windows = self.browser.get_window_handles()
                self.browser.switch_window(windows[0])
                self.browser.click_element_when_visible('//div/ul/li/a[text()="Billing"]')
                return
            self.send_to_gateway()

        windows = self.browser.get_window_handles()
        self.browser.switch_window(windows[0])

        self.apply_bulk_payment('Claim #{}'.format(', '.join(list_of_claims_id)))

    def get_timesheets_id(self) -> list:
        # Prepare dict of timesheets for processing
        rows: list = self.browser.find_elements('//tr[contains(@id, "billing-grid-row-")]')
        timesheets_id: list = []
        for row in rows:
            timesheets_id.append(row.get_attribute('id').split('-')[-1])
        return timesheets_id

    def cr_main_process(self):
        common.log_message('Starting Billing Prep')

        headers_index: dict = self.find_header_index(
            ['client', 'date', 'time', 'payor', 'providers', 'service/auth', 'location', 'options']
        )
        if self.browser.does_page_contain_element('//a[@data-click="closeMenu"]') and \
                self.browser.find_element('//a[@data-click="closeMenu"]').is_displayed():
            self.browser.click_element_when_visible('//a[@data-click="closeMenu"]')

        common.log_message('Starting processing timesheets')
        list_of_timesheets_id = self.get_timesheets_id()
        valid_ts_id: dict = {}
        for timesheet_id in list_of_timesheets_id:
            columns: list = self.browser.find_elements(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td')
            service_name: str = str(columns[headers_index['service/auth']].text).strip()

            if str(columns[headers_index['tasks']].text).strip():
                continue
            if '97153' not in service_name and '97155' not in service_name:
                continue

            # Performing authorization check
            common.log_message(f'Timesheet ID { timesheet_id }. Performing the authorization check')
            date: str = str(columns[headers_index['date']].text).strip()
            self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/div/button')
            self.browser.click_element_when_visible(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/div/button')
            common.wait_element(self.browser, f'//tr[@id="billing-grid-row-{ timesheet_id }"]//li[text()="Entry ID: "]')

            auth_number: str = ''
            auth_start_date: str = ''
            auth_end_date: str = ''
            auth_code: str = ''
            common.wait_element(self.browser, f'//tr[@id="billing-grid-row-{ timesheet_id }"]//a[@data-toggle="timesheet-preview"]')
            for elem in self.browser.find_elements(f'//tr[@id="billing-grid-row-{ timesheet_id }"]//a[@data-toggle="timesheet-preview"]'):
                try:
                    elem.click()
                    break
                except:
                    pass
            try:
                common.wait_element(self.browser, '//a[text()="Authorization"]')
                if self.browser.does_page_contain_element('//a[text()="Authorization"]'):
                    self.browser.click_element_when_visible('//a[text()="Authorization"]')
                    common.wait_element(self.browser, '//span[contains(@data-bind, "authorizationNumber")]')
                    auth_number = str(self.browser.get_text('//span[contains(@data-bind, "authorizationNumber")]')).strip()
                    auth_start_date = self.browser.get_text('//span[contains(@data-bind, "authorizationStartDate")]').strip()
                    auth_end_date = self.browser.get_text('//span[contains(@data-bind, "authorizationEndDate")]').strip()
                    auth_code = self.browser.get_text('//div[contains(@data-bind, "authorizedCode")]').strip().split(':')[0]
            except Exception as ex:
                common.log_message(str(ex), 'ERROR')
            finally:
                if self.browser.does_page_contain_element('//button[@class="close padding-right"]'):
                    self.browser.click_element_when_visible('//button[@class="close padding-right"]')
                    self.browser.wait_until_element_is_not_visible('//button[@class="close padding-right"]')
            self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/input')

            is_date_match: bool = False
            if auth_start_date and auth_end_date:
                is_date_match = datetime.datetime.strptime(auth_start_date, '%m/%d/%Y') <= datetime.datetime.strptime(date, '%m/%d/%y') <= datetime.datetime.strptime(auth_end_date, '%m/%d/%Y')

            # Performing location and timing check
            common.log_message(f'Timesheet ID { timesheet_id }. Performing the location and timing check')
            location_from_web: str = columns[headers_index['location']].text
            is_location_match: bool = False
            is_time_match: bool = False
            if columns[headers_index['file']].text:
                link_to_pdf = columns[headers_index['file']].find_element_by_tag_name('a').get_attribute('href')
                time_from_web = columns[headers_index['time']].text
                is_location_match, is_time_match = self.download_and_validate_pdf(link_to_pdf, location_from_web, time_from_web)

            # Create task if something not valid
            if self.is_need_task(auth_number, is_date_match, is_location_match, is_time_match, service_name.startswith(auth_code), timesheet_id):
                continue
            else:
                valid_ts_id[timesheet_id] = {'date': date, 'service': service_name}

        if len(valid_ts_id) == 0:
            common.log_message('Unable to generate claim. All timesheets have mistakes.')
            return

        count_unique: int = 0
        count_total_selected: int = 0
        selected_rows: list = []
        for timesheet_id in valid_ts_id:
            is_selected: bool = False
            try_count: int = 0
            while not is_selected and try_count < 5:
                try_count += 1
                try:
                    self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/input')
                    common.wait_element(self.browser, f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/input')
                    self.browser.select_checkbox(f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/input')
                    is_selected = True
                except:
                    self.browser.execute_javascript('window.scrollBy(0,-42)')
                    is_selected = False
            count_total_selected += 1
            if '{}|{}'.format(valid_ts_id[timesheet_id]['date'], valid_ts_id[timesheet_id]['service']) not in selected_rows:
                selected_rows.append('{}|{}'.format(valid_ts_id[timesheet_id]['date'], valid_ts_id[timesheet_id]['service']))
                count_unique += 1
            if count_unique == 6 or count_total_selected == len(valid_ts_id):
                self.generate_claim()
                selected_rows: list = []
                count_unique = 0
                common.wait_element(self.browser, f'//tr[@id="billing-grid-row-{ timesheet_id }"]/td/input')
                if count_total_selected != len(valid_ts_id):
                    for timesheet_id_temp in valid_ts_id:
                        self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{ timesheet_id_temp }"]/td/input')
                        self.browser.unselect_checkbox(f'//tr[@id="billing-grid-row-{ timesheet_id_temp }"]/td/input')

    def click_action_and_bulk_merge_claims(self) -> None:
        common.wait_element(self.browser, '//a[contains(., "Action")]')
        self.browser.click_element_when_visible('//a[contains(., "Action")]')

        common.wait_element(self.browser, '//a[contains(., "Bulk-merge Claims")]')
        self.browser.click_element_when_visible('//a[contains(., "Bulk-merge Claims")]')

        common.wait_element(self.browser, '//a[contains(@data-bind, "expandClaimsInfoClick")]', 5, False)
        if self.browser.does_page_contain_element('//button[text()="Merge"]'):
            if self.browser.find_element('//button[text()="Merge"]').is_displayed():
                self.browser.click_element_when_visible('//button[text()="Merge"]')

    def bulk_merge_claims(self):
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

        self.browser.select_checkbox('//input[contains(@data-bind, "includeTimes")]')

    def sync_provider_supplier_to_provider(self):
        gears = self.browser.find_elements(
            '//th[contains(.,"Provider Supplier")]/div/div/ul/li/a[text()="To provider"]/../../../a/i')
        to_elem = self.browser.find_elements('//th[contains(.,"Provider Supplier")]//a[text()="To provider"]')
        for index in range(len(gears)):
            gears[index].click()
            time.sleep(1)
            to_elem[index].click()

    def generating_claims(self) -> (str, list):
        self.bulk_merge_claims()
        self.sync_provider_supplier_to_provider()

        self.browser.click_element_when_visible('//a[text()="Combined Claims View"]')
        common.wait_element(self.browser, '//li[@class="active"]/a[text()="Combined Claims View"]')

        payor: str = str(self.browser.get_text('//span[contains(@data-bind, "insuranceName")]')).strip()

        def input_location(location_code):
            self.browser.click_element_when_visible('//th[contains(.,"Location")]/div/a[contains(@data-bind, "{title: \'Search for different provider\'}")]')
            common.wait_element(self.browser, '//th[contains(.,"Location")]/div/div/input')
            self.browser.input_text_when_element_is_visible('//th[contains(.,"Location")]/div/div/input', location_code)
            self.browser.click_element_when_visible('//li/div[contains(.,"' + location_code + '")]')

        temp_payor = payor.lower()
        if 'United Healthcare'.lower() in temp_payor or 'United Behavioral Health'.lower() in temp_payor or \
                'UMR'.lower() in temp_payor or 'UBH'.lower() in temp_payor:
            input_location('26310')
        # if 'Blue Cross Blue Shield' in payor:
        #     input_location('26310')  # TBD

        self.browser.click_element_when_visible('//button[contains(., "Start claims generation")]')
        common.wait_element(self.browser, '//a[contains(.,"Go to claims inbox") and contains(@data-bind, "visible: $root.bulkClaimsVm.processingComplete()")]')

        list_of_claims_url: list = []
        claims: list = self.browser.find_elements('//a[contains(@data-bind, "&&claimId()!=-1")]')
        for item in claims:
            if item.is_displayed():
                list_of_claims_url.append(item.get_attribute('href'))

        return payor, list_of_claims_url

    def apply_bulk_payment(self, claim_num):
        click_bunch_of_elements(
            browser=self.browser,
            paths=[
                '//div/ul/li/a[text()="Billing"]',
                '//a[@id="btnBillingPayment"]',
                '//tr[@class="controls"]/td[1]/span',
                '//table[@class="ui-datepicker-calendar"]//td[@class=" ui-datepicker-days-cell-over  ui-datepicker-today"]',
                '//tr[@class="controls"]/td[2]/select/option[@value="7"]',
            ]
        )
        self.browser.input_text('//tr[@class="controls"]/td[5]/input[@data-bind="value: notes"]', 'BILLED {}'.format(claim_num))

        # press Apply payment
        common.wait_element(self.browser, "//button[text()='Apply Payments']")
        self.browser.click_element_when_visible("//button[text()='Apply Payments']")

        common.wait_element(self.browser, "//span[text()='All payments applied successfully']", timeout=15, is_need_screen=False)
        try:
            is_success = self.browser.find_element("//span[text()='All payments applied successfully']")
            if not is_success.is_displayed():
                common.log_message('Not all payments applied successfully', 'ERROR')
                self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', '{}_payments_failed.png'.format(claim_num)))
        except:
            pass
        self.browser.click_element_when_visible('//div[contains(@data-bind, "bulk-payments")]//a[text()="Back to billing"]')

    def disposition_provider(self) -> list:
        common.wait_element(self.browser, '//a[contains(., "Provider/Supplier")]')
        self.browser.click_element_when_visible('//a[contains(., "Provider/Supplier")]')

        bcba = self.browser.get_value('//input[@id="providers-rendering-specialtycode"]')
        if not bcba:
            return ['Provider/Supplier: BCBA is missing']
        return []

    def disposition_facility(self, payor) -> list:
        common.wait_element(self.browser, '//a[contains(., "Facility")]')
        self.browser.click_element_when_visible('//a[contains(., "Facility")]')

        temp_payor = payor.lower()
        if 'Aetna'.lower() in temp_payor or 'Cigna'.lower() in temp_payor or 'Humana'.lower() in temp_payor or \
                'LA Medicaid'.lower() in temp_payor:
            if self.browser.does_page_contain_element('//abbr[@data-column="FacilityName"]/../..//abbr[@class="select2-search-choice-close"]'):
                self.browser.click_element_when_visible('//abbr[@data-column="FacilityName"]/../..//abbr[@class="select2-search-choice-close"]')
                return []
        elif 'United Healthcare'.lower() in temp_payor or 'United Behavioral Health'.lower() in temp_payor or \
                'UMR'.lower() in temp_payor or 'UBH'.lower() in temp_payor:
            return []

        def is_field_empty(locator):
            field_class = self.browser.get_element_attribute(
                locator=locator,
                attribute='class'
            )
            if 'error' in field_class:
                return True
            return False

        errors: list = []
        if is_field_empty('//input[@id="providers-facility-address1"]'):
            errors.append('Address is missing')
        if is_field_empty('//input[@id="providers-facility-city"]'):
            errors.append('City is missing')
        if is_field_empty('//input[@id="providers-facility-zip"]'):
            errors.append('Zip is missing')
        if is_field_empty('//select[@id="providers-facility-state"]'):
            errors.append('State is missing')
        return errors

    def disposition_patient(self) -> list:
        common.wait_element(self.browser, '//span[text()="Patient"]')
        self.browser.click_element_when_visible('//span[text()="Patient"]')

        common.wait_element(self.browser, '//a[contains(., "Subscriber")]')
        self.browser.click_element_when_visible('//a[contains(., "Subscriber")]')

        errors: list = []
        errors_subscriber = self.browser.find_elements('//div[@id="patient-subscriber"]//*[@class="form-control error"]')
        if len(errors_subscriber) > 0:
            errors.append('Subscriber is not fully populated')
        errors_patient = self.browser.find_elements('//div[@id="patient-patient"]//*[@class="form-control error"]')
        if len(errors_patient) > 0:
            errors.append('Patient is not fully populated')
            return errors
        subscriber_birthday: str = self.browser.get_value('//input[@id="patient-subscriber-birthdate"]')
        if subscriber_birthday:
            year, month, day = common.convert_date(subscriber_birthday)
            subscriber_birthday = common.convert_time_new(0, 0, year, month, day, 'a', 'EST')
        else:
            errors.append('Birthday of subscriber is missing')

        patient_birthday: str = self.browser.get_value('//input[@id="patient-patient-birthdate"]')
        if patient_birthday:
            year, month, day = common.convert_date(patient_birthday)
            patient_birthday = common.convert_time_new(0, 0, year, month, day, 'a', 'EST')
        else:
            errors.append('Birthday of patient is missing')
            return errors

        self.browser.click_element_when_visible('//a[contains(., "Patient")]')
        if patient_birthday == subscriber_birthday:
            click_element(self.browser, '//select[@id="patient-insurance-relationship"]/option[@value="18"]')
        else:
            click_element(self.browser, '//select[@id="patient-insurance-relationship"]/option[@value="19"]')
        return errors

    def disposition_auth(self) -> list:
        common.wait_element(self.browser, '//span[text()="Claim"]')
        self.browser.click_element_when_visible('//span[text()="Claim"]')

        auth: str = self.browser.get_value('//input[contains(@data-bind, "priorAuthorization")]')
        if not auth:
            return ['Auth# is missing']
        return []

    def save_claim(self):
        self.browser.click_element_when_visible('//button[contains(., "Save Claim")]')
        self.browser.wait_until_element_is_not_visible('//span[text()="Saving"]')

    def assign_task_claims(self, assign_task_to: str, task_description: str):
        click_bunch_of_elements(
            browser=self.browser,
            paths=[
                '//button[contains(., "Actions")]',
                '//a[text()="Add Tasks"]'
            ]
        )

        self.browser.input_text_when_element_is_visible('//input[@placeholder="Name of new task"]', 'Review Claim Errors')
        self.browser.input_text_when_element_is_visible('//textarea[@placeholder="Optional description"]', task_description)
        click_element(self.browser, '//div[@class="col-sm-6"]/select/option[@value="1"]')
        click_element(self.browser, '//div[@class="select2-search"]/input[@placeholder="Select a person or a label"]')
        self.browser.input_text_when_element_is_visible(
            locator='//div[@class="select2-search"]/input[@placeholder="Please enter 3 more characters..."]',
            text=assign_task_to
        )
        list_locator = '//div[@class="form-group"]//li[@class="select2-result select2-result-selectable select2-highlighted"]'
        common.wait_element(
            browser=self.browser,
            selector=list_locator
        )
        if (self.browser.does_page_contain_element(
                locator=list_locator
        )):
            keys = (False, 'RETURN')
            self.browser.press_keys(*keys)

        self.browser.click_element_when_visible('//button[@id="btn-create-task"]')
        self.browser.wait_until_element_is_not_visible('//button[@id="btn-create-task"]')

    def send_to_gateway(self):
        click_bunch_of_elements(
            browser=self.browser,
            paths=[
                '//button[contains(., "Actions")]',
                '//a[text()="Send to Gateway"]',
            ])
        common.wait_element(self.browser, '//input[@id="ignoreError2"]')
        self.browser.select_checkbox('//input[@id="ignoreError2"]')
        try:
            self.browser.click_element_when_visible('//button[text()="Send to gateway"]')
        except Exception as ex:
            print(str(ex))
            self.browser.select_checkbox('//input[@id="ignoreError2"]')
            time.sleep(1)
            self.browser.click_element_when_visible('//button[text()="Send to gateway"]')
