from RPA.Tables import Table
from RPA.Browser.Selenium import Selenium
from libraries import common
from libraries.timesheet import Timesheet
from urllib.parse import urlparse
import datetime
import time
import os
import shutil
import re
from libraries.excel import CsvInterface
from libraries.excel import ExcelInterface


class CentralReach:
    billable_claims_filter_name = 'BILLABLE CLAIMS v2'
    billing_scrub_filter_name = 'BILLING SCRUB v2'

    def __init__(self, credentials: dict):
        self.browser: Selenium = Selenium()
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.employee_id: str = ''
        self.login_to_central_reach()
        self.base_url = self.get_base_url()
        self.start_date: datetime = None
        self.end_date: datetime = None
        self.mapping: ExcelInterface or None = None
        self.trump_site_list: list or None = None
        self.domo_mapping_file: dict = {}
        self.domo_mapping_site: dict = {}
        self.overlap_check_clients = {}
        self.modifiers_check_error_list_with_id: list = []

    def get_base_url(self):
        parsed_uri = urlparse(self.url)
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

    def login_to_central_reach(self):
        self.browser.close_all_browsers()
        self.browser.timeout = 30
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
                common.wait_element(self.browser, "//input[@type='password']", is_need_screen=False, timeout=10)
                if self.browser.does_page_contain_element("//p[text()='Scheduled Maintenance']"):
                    if self.browser.find_element("//p[text()='Scheduled Maintenance']").is_displayed():
                        common.log_message("Logging into CentralReach failed. Scheduled Maintenance.", 'ERROR')
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
                self.browser.wait_and_click_button("//button[@class='btn']")
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
        if self.is_site_available:
            self.employee_id = str(self.browser.get_text("//span/span[text()='Employee']/../../span[@class='pull-right']")).strip()
            self.open_new_tab()

    def open_new_tab(self):
        # Open new tab for processing
        self.browser.execute_javascript("window.open('" + self.url + "');")
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])
        self.browser.set_window_size(1920, 1080)
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

    @staticmethod
    def calculate_date(run_date=''):
        if len(run_date) > 0:
            prior_day = datetime.datetime.strptime(run_date, '%m/%d/%Y')
            start_date, end_date = prior_day, prior_day
        else:
            prior_day = datetime.datetime.utcnow() + datetime.timedelta(days=-7)
            start_date = prior_day
            end_date = prior_day

            # Monday is 0 and Sunday is 6
            if prior_day.weekday() == 0:
                start_date = prior_day + datetime.timedelta(days=-1)
            elif prior_day.weekday() == 4:
                end_date = prior_day + datetime.timedelta(days=1)
        print('Start date: {}. End date: {}'.format(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        return start_date, end_date

    def apply_filter(self, filter_name: str, additional_params='', sort_by_client=False):
        # Go to billing page
        self.browser.go_to(self.base_url + '#billingmanager/billing/?startdate={}&enddate={}'.format(
            self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d')))
        common.wait_element(self.browser, "//th[contains(.,'Payor')]/a/i")

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
        if sort_by_client:
            updated_url = re.sub(r'sort=\w+', 'sort=client', updated_url)
        updated_url += additional_params
        updated_url = re.sub(r'startdate=\d{4}-\d{2}-\d{2}', self.start_date.strftime('startdate=%Y-%m-%d'), updated_url)
        updated_url = re.sub(r'enddate=\d{4}-\d{2}-\d{2}', self.end_date.strftime('enddate=%Y-%m-%d'), updated_url)

        self.browser.go_to(updated_url)
        self.browser.go_to(updated_url)

        self.browser.wait_until_element_is_not_visible("//em[text()='Agreed charges: <loading>']", datetime.timedelta(seconds=60))
        date_range = '{} - {}'.format(self.start_date.strftime('%b %d'), self.end_date.strftime('%b %d'))
        if not self.browser.does_page_contain_element('//span[text()="' + date_range + '"]'):
            self.browser.go_to(updated_url)
            self.browser.wait_until_element_is_not_visible("//em[text()='Agreed charges: <loading>']", datetime.timedelta(seconds=60))

    def find_header_index(self, required_headers: list) -> dict:
        headers_index = {}
        find_headers = self.browser.find_elements("//thead/tr[@class='white']")

        for row in find_headers:
            count = 0
            for header in required_headers:
                if header.lower() in row.text.lower():
                    count += 1
            if count == len(required_headers):
                headers_columns = row.find_elements_by_tag_name("th")
                for column_name in headers_columns:
                    tmp_column_name = column_name.text.lower()
                    if tmp_column_name in required_headers and tmp_column_name not in headers_index:
                        headers_index[tmp_column_name] = headers_columns.index(column_name)
                    if tmp_column_name == 'agreed' and tmp_column_name in headers_index:
                        headers_index['charges_agreed'] = headers_columns.index(column_name)
                break
        return headers_index

    def apply_label(self, label_add: str, label_remove: str):
        common.wait_element(self.browser, '//button[contains(., "Label selected")]')
        self.browser.click_element_when_visible('//button[contains(., "Label selected")]')

        if len(label_add) > 0:
            common.wait_element(self.browser, '//h4[text()="Apply Labels"]/../../div/div/ul/li/input')
            self.browser.input_text('//h4[text()="Apply Labels"]/../../div/div/ul/li/input', label_add)
            common.wait_element(self.browser, '//div[text()="' + label_add + '" and @role="option"]')
            if self.browser.does_page_contain_element(
                    "//div[@id='select2-drop']/ul[@class='select2-results']/li[@class='select2-no-results']"):
                self.browser.input_text('//h4[text()="Apply Labels"]/../../div/div/ul/li/input', label_add.lower())
                common.wait_element(self.browser, '//div[text()="' + label_add + '" and @role="option"]')
            self.browser.click_element_when_visible('//div[text()="' + label_add + '" and @role="option"]')
        if len(label_remove) > 0:
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

    def change_provider_to_all_claims(self, column_name: str, provider_name: str):
        self.browser.click_element_when_visible('//th[contains(.,"' + column_name + '")]/div/a[contains(@data-bind, "{title: \'Search for different provider\'}")]')

        common.wait_element(self.browser, '//th[contains(.,"' + column_name + '")]/div/div/input')
        self.browser.input_text_when_element_is_visible('//th[contains(.,"' + column_name + '")]/div/div/input', provider_name)

        common.wait_element(self.browser, '//li/div[contains(.,"' + provider_name + '")]')
        self.browser.click_element_when_visible('//li/div[contains(.,"' + provider_name + '")]')

        self.sync_to_all_claims(column_name)

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
            common.log_message(str(ex), 'ERROR')
            self.browser.capture_page_screenshot(
                os.path.join(os.environ.get(
                    "ROBOT_ROOT", os.getcwd()),
                    'output',
                    'Validate_provider_error_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
                )
            )
        finally:
            self.browser.switch_window(browser_tabs[0])

    def change_provider_by_id(self, column_name: str, provider_id: str) -> bool:
        if not self.search_provider_by_id(column_name, provider_id):
            return False
        else:
            self.sync_to_all_claims(column_name)
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

    def start_claims_generation(self):
        self.browser.click_element_when_visible('//a[text()="Combined Claims View"]')
        common.wait_element(self.browser, '//li[@class="active"]/a[text()="Combined Claims View"]')

        self.browser.click_element_when_visible('//button[contains(., "Start claims generation")]')
        common.wait_element(self.browser, '//a[contains(.,"Go to claims inbox") and contains(@data-bind, "visible: $root.bulkClaimsVm.processingComplete()")]', 60*3)
        if not self.browser.does_page_contain_element('//a[contains(.,"Go to claims inbox") and contains(@data-bind, "visible: $root.bulkClaimsVm.processingComplete()")]'):
            common.log_message('The bot waited for 3 minutes, but the claim was never generated', 'ERROR')

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

    def check_domo_provider_id(self, providers_id: list, insurance_name: str) -> str:
        providers_id = sorted(providers_id, key=lambda i: i['hours'], reverse=True)
        provider_id = ''

        for provider in providers_id:
            try:
                browser_tabs = self.browser.get_window_handles()
                self.browser.switch_window(browser_tabs[1])

                # Update insurance name
                if insurance_name.lower().strip() in self.mapping.bcba_mapping:
                    tmp_insurance_name = self.mapping.bcba_mapping[insurance_name.lower().strip()]
                else:
                    return provider['clinician_id']

                list_of_insurances: list = []
                for insurance in tmp_insurance_name.split('&'):
                    list_of_insurances.append(str(insurance).strip())

                self.browser.go_to(
                    'https://members.centralreach.com/#resources/templatesreport/?templateId=3997&contactId={}'.format(
                        provider['clinician_id'])
                )
                common.wait_element(self.browser, '//em[contains(.,"Provider ID:") or contains(.,"Not Found")]')
                if self.browser.does_page_contain_element('//em[contains(.,"Not Found")]'):
                    continue

                self.uncheck_all_credentials_fields()

                for insurance in list_of_insurances:
                    all_items = self.browser.find_elements('//span[@class="ag-column-select-label"]')
                    for item in all_items:
                        if insurance.lower() == item.text.lower():
                            item.click()
                            break

                if self.browser.does_page_contain_element('//div[@class="dropdown"]/div/a[contains(., "file")]'):
                    if len(self.browser.find_elements('//div[@class="dropdown"]/div/a[contains(., "file")]')) == \
                            len(list_of_insurances):
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

    def get_client_location(self, client_id: str, insurance_name: str) -> str:
        location = ''
        self.browser.click_element_when_visible('//a[@contactid="' + client_id + '"]')
        common.wait_element(self.browser, '//small[text()="Upload File"]')
        common.wait_element(self.browser, '//a[text()=" Labels"]', timeout=10, is_need_screen=False)
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
            common.wait_element(self.browser, '//a[text()=" Labels"]', timeout=10, is_need_screen=False)
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

    def check_and_update_billing(self, valid_billing: str, full_billing_name: str):
        all_billings = self.browser.find_elements('//a[contains(@data-bind, "billingName")]')
        for billing in all_billings:
            if valid_billing.lower() not in str(billing.text).lower():
                self.change_billing('Billing', full_billing_name)
                break

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
        is_bcba_exist: bool = False
        valid_index: int = -1
        bcba_ids: list = []

        all_procedure_code = self.browser.find_elements('//span[contains(@data-bind, "procedureCodeString() || procedureCode()")]')
        for procedure_code in all_procedure_code:
            procedure_code_text: str = str(procedure_code.text).lower()
            for valid_code in ['BCBA', '97151', '97155', '97156', '97158', '90889', 'H0031', 'H0032', 'H2021', 'T1023']:
                if valid_code.lower() in procedure_code_text:
                    provider_id: str = self.browser.find_element(f'(//a[contains(@data-bind, "providerName")])[{all_procedure_code.index(procedure_code) + 1}]').get_attribute('data-contactid')
                    if provider_id not in bcba_ids:
                        bcba_ids.append(provider_id)
                    if valid_index == -1:
                        valid_index = all_procedure_code.index(procedure_code)
                    break

        if valid_index != -1 and len(bcba_ids) == 1:
            if 'United Behavioral Health'.lower() == insurance_name.lower().strip():
                providers_all: list = self.browser.find_elements('//a[contains(@data-bind, "providerName")]')
                provider_id: str = providers_all[valid_index].get_attribute('data-contactid')
                is_bcba_exist = self.change_provider_by_id('Provider', provider_id)
            else:
                sync_all: list = self.browser.find_elements('//a[contains(@data-bind, "syncField") and @data-syncfield="provider"]')
                sync_all[valid_index].click()
                is_bcba_exist = True

        if not is_bcba_exist:
            is_bcba_exist = self.find_domo_provider_id_and_change(client_id, insurance_name)

        if is_bcba_exist:
            self.sync_provider_to_provider_supplier()
        return is_bcba_exist

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

    def prepare_claims_to_generate(self,
                                   insurance_name: str,
                                   client_id: str,
                                   location: str,
                                   list_of_providers=None
                                   ) -> bool:
        insurance_name = insurance_name.lower()
        if self.does_need_skip_insurance(insurance_name):
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
            if 'Blue Cross Blue Shield of Colorado'.lower() in insurance_name or 'Anthem CO'.lower() in insurance_name:
                self.browser.select_checkbox('//input[contains(@data-bind, "includeTimes")]')
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
            modifier_key: str = '76'
            end_index: int = 1
            if len(list_of_providers) > 1 and ('Humana'.lower() in insurance_name.lower() or 'Tricare'.lower() in insurance_name.lower()):
                modifier_key: str = '77'
                end_index: int = 0
            modifiers = self.browser.find_elements('//input[@data-bind="value: modifier1"]')
            for index in range(len(modifiers) - end_index):
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

    def post_claims_generation_and_apply_label(self, insurance_name: str):
        # check claims
        if 'Cigna'.lower() in insurance_name or 'Contra Costa'.lower() in insurance_name \
                or 'Beacon Line Construction Benefit Fund'.lower() in insurance_name:
            list_of_claims_url = []
            claims = self.browser.find_elements('//a[contains(@data-bind, "&&claimId()!=-1")]')
            for item in claims:
                if item.is_displayed():
                    list_of_claims_url.append(item.get_attribute('href'))
            if len(list_of_claims_url) > 0:
                if 'Contra Costa'.lower() in insurance_name \
                        or 'Beacon Line Construction Benefit Fund'.lower() in insurance_name:
                    self.update_claims_address(list_of_claims_url)
                elif 'Cigna'.lower() in insurance_name:
                    self.validate_prior_authorization(list_of_claims_url)

        # apply label
        self.browser.click_element_when_visible('//div/ul/li/a[text()="Billing"]')
        if 'Contra Costa'.lower() in insurance_name or 'Beacon Line Construction Benefit Fund'.lower() in insurance_name:
            self.apply_label('CSPAPER', 'Ready to bill')
        else:
            self.apply_label('CSELEC', 'Ready to bill')

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

    def select_insurance_from_list(self, insurance_name: str, list_of_valid_insurances: list) -> None:
        # Open 'Insurances' window
        common.click_and_wait(
            browser=self.browser,
            locator_for_click="//th[contains(.,'Payor')]/a/i",
            locator_for_wait="//div/span[text()='insurances']"
        )

        for insurance_name_tmp in list_of_valid_insurances:
            try:
                common.wait_element(
                    browser=self.browser,
                    locator='//a/span[text()=("' + insurance_name_tmp + '")]/..',
                    timeout=5,
                    is_need_screen=False
                )
                if self.browser.does_page_contain_element('//a/span[text()=("' + insurance_name_tmp + '")]/..'):
                    self.browser.scroll_element_into_view('//a/span[text()=("' + insurance_name_tmp + '")]/..')
            except Exception as ex:
                common.log_message('Scroll into view error: ' + str(ex), 'TRACE')
            finally:
                if insurance_name == insurance_name_tmp:
                    break
        self.browser.click_element_when_visible('//a/span[text()=("' + insurance_name + '")]/..')
        common.wait_element(self.browser, '//em[contains(.,"Insurance: ' + insurance_name.strip() + '")]')

    def prepare_billing_scrub(self) -> list:
        self.apply_filter(self.billable_claims_filter_name)

        if self.is_no_results('No results matched {} filter and date range'.format(self.billable_claims_filter_name)):
            return []

        # Open 'Insurances' and 'Clients' window
        common.click_and_wait(
            browser=self.browser,
            locator_for_click="//th[contains(.,'Payor')]/a/i",
            locator_for_wait="//div/span[text()='insurances']"
        )
        self.open_window_with_clients()

        common.wait_element(self.browser, "//div/span[text()='insurances']/../../div/ul/li")
        all_insurances = self.browser.find_elements("//div/span[text()='insurances']/../../div/ul/li")

        list_of_valid_insurances: list = []
        for insurance in all_insurances:
            insurance_name = str(insurance.text)
            if self.does_need_skip_insurance(insurance_name):
                continue

            if len(insurance_name) > 0 and not insurance_name.startswith('>'):
                list_of_valid_insurances.append(str(insurance.find_element_by_tag_name('span').get_attribute('innerHTML')))
        return list_of_valid_insurances

    def validate_multiply_providers(self) -> dict:
        # Get timesheets id by provider - only 97151, 97155 or 97156
        headers_index: dict = self.find_header_index(['client', 'providers', 'payor', 'service/auth'])
        rows: list = self.browser.find_elements('//tr[contains(@id, "billing-grid-row-")]')
        timesheets_by_provider: dict = {}
        for row in rows:
            service: str = row.find_elements_by_tag_name('td')[headers_index['service/auth']].text
            service = service.split(':')[0]
            if service.strip().upper() not in ['97151', '97155', '97156']:
                continue
            provider: str = row.find_elements_by_tag_name('td')[headers_index['providers']].text
            if provider not in timesheets_by_provider:
                timesheets_by_provider[provider] = []
            timesheets_by_provider[provider].append(row.get_attribute('id').split('-')[-1])
        if not timesheets_by_provider:
            timesheets_by_provider[''] = ''
        return timesheets_by_provider

    def select_unselect_checkboxes(self, timesheets_id: list, is_need_select: bool = True) -> None:
        for timesheet_id in timesheets_id:
            xpath: str = f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/input'
            self.browser.scroll_element_into_view(xpath)
            checkbox = self.browser.find_element(xpath)
            if not self.browser.is_checkbox_selected(xpath) and is_need_select:
                self.browser.driver.execute_script("arguments[0].click();", checkbox)
            if self.browser.is_checkbox_selected(xpath) and not is_need_select:
                self.browser.driver.execute_script("arguments[0].click();", checkbox)

    def unselect_all_checkboxes(self) -> None:
        for checkbox in self.browser.find_elements('//tr[contains(@id, "billing-grid-row-")]/td/input'):
            if self.browser.is_checkbox_selected(checkbox):
                self.browser.driver.execute_script("arguments[0].click();", checkbox)

    def billing_scrub(self) -> None:
        list_of_valid_insurances: list = self.prepare_billing_scrub()

        for insurance_name in list_of_valid_insurances:
            common.log_message(f'{insurance_name} processing has been started')

            # START TEST
            # if 'CO Medicaid'.lower() not in insurance_name.lower():
            #     continue
            # END TEST

            claims_generated = 0
            try:
                self.select_insurance_from_list(insurance_name, list_of_valid_insurances)
                # Open 'Clients' window
                self.open_window_with_clients()
                list_of_valid_clients: list = self.get_list_of_clients()
                self.browser.reload_page()
                self.open_window_with_clients()

                for client_name in list_of_valid_clients:
                    try:
                        self.open_window_with_clients()
                        client_id: str = self.select_client_from_list(client_name)

                        # Select all timesheets
                        checkbox = self.browser.find_element('//input[@data-bind="checked: listVm.allSelected"]')
                        self.browser.driver.execute_script("arguments[0].click();", checkbox)

                        if client_id in self.modifiers_check_error_list_with_id:
                            common.log_message(f'The client {client_id} was skipped because the error occurred earlier.')
                            continue

                        location = ''
                        if 'CO Medicaid'.lower() in insurance_name.lower():
                            location = self.get_client_location(client_id, 'CO Medicaid')

                        # New requirements
                        if 'Tricare'.lower() in insurance_name or 'Humana'.lower() in insurance_name:
                            timesheets_by_provider: dict = {'': ''}
                        else:
                            timesheets_by_provider: dict = self.validate_multiply_providers()
                            if len(timesheets_by_provider) > 1:
                                common.log_message(f"Found {len(timesheets_by_provider)} different BCBA's. Client {client_name} [{client_id}]", 'WARN')

                        processed: int = 0
                        for provider in timesheets_by_provider:
                            if provider == list(timesheets_by_provider.keys())[processed] and processed > 0:
                                self.unselect_all_checkboxes()
                                self.select_unselect_checkboxes(timesheets_by_provider[provider], True)
                            processed += 1
                            if processed == len(timesheets_by_provider) + 1:
                                break
                            for provider_second in list(timesheets_by_provider.keys())[processed:]:
                                self.select_unselect_checkboxes(timesheets_by_provider[provider_second], False)

                            # Generate claim
                            self.bulk_merge_claims(insurance_name)

                            if not self.prepare_claims_to_generate(insurance_name, client_id, location):
                                self.browser.click_element_when_visible('//div/ul/li/a[text()="Billing"]')
                                self.browser.reload_page()
                                continue

                            # START TEST
                            # self.browser.click_element_when_visible('//div/ul/li/a[text()="Billing"]')
                            # END TEST

                            # click start claims generation
                            self.start_claims_generation()
                            claims_generated += 1

                            common.custom_logger(f'Claim generated successfully. Client: {client_name} [{client_id}]')
                            common.google_logger.update_spreadsheet(
                                datetime.datetime.utcnow().strftime('%I:%M:%S %p'),
                                'INFO',
                                f'Claim generated successfully. Client: {client_name} [{client_id}]'
                            )

                            self.post_claims_generation_and_apply_label(insurance_name.lower())

                    except Exception as client_error:
                        common.log_message(str(client_error), 'ERROR')
                        self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output','Something_went_wrong_{}.png'.format(str(client_name).replace('"', '').replace("'", ""))))

                        if self.browser.does_page_contain_element("//input[@type='password']"):
                            common.log_message(f'ERROR: {client_name} processing failed. An unexpected error occurred and the bot was logged out.', 'ERROR')
                            self.login_to_central_reach()
                            self.apply_filter(self.billable_claims_filter_name)
                            self.select_insurance_from_list(insurance_name, list_of_valid_insurances)
                        elif 'element click intercepted' in str(client_error):
                            common.log_message(f'ERROR: {client_name} processing failed. Looks like there is a new popup we need to close.', 'ERROR')
                        elif 'not visible after' in str(client_error):
                            common.log_message(f'ERROR: {client_name} processing failed. Looks like the required element did not appear.', 'ERROR')
                        else:
                            common.log_message(f'ERROR: {client_name} processing failed. Something went wrong.', 'ERROR')

                        browser_tabs = self.browser.get_window_handles()
                        self.browser.switch_window(browser_tabs[0])

                        try:
                            if self.browser.does_page_contain_element('//div/ul/li/a[text()="Billing"]'):
                                if self.browser.find_element('//div/ul/li/a[text()="Billing"]').is_displayed():
                                    self.browser.click_element_when_visible('//div/ul/li/a[text()="Billing"]')
                        except Exception as exc:
                            common.log_message(str(exc), 'ERROR')

                # remove client and insurance filter
                self.apply_filter(self.billable_claims_filter_name)
                common.log_message('{} processing is completed. Claims for {} clients have been successfully generated'.format(insurance_name, claims_generated))
            except Exception as insurance_error:
                common.log_message(str(insurance_error), 'ERROR')
                self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', f'Something_went_wrong_{insurance_name.strip()}.png'))

                if self.browser.does_page_contain_element("//input[@type='password']"):
                    common.log_message(f'ERROR: {insurance_name} processing failed. An unexpected error occurred and the bot was logged out.', 'ERROR')
                    self.login_to_central_reach()
                elif 'element click intercepted' in str(insurance_error):
                    common.log_message(f'ERROR: {insurance_name} processing failed. Looks like there is a new popup we need to close.', 'ERROR')
                elif 'not visible after' in str(insurance_error):
                    common.log_message(f'ERROR: {insurance_name} processing failed. Looks like the required element did not appear.', 'ERROR')
                else:
                    common.log_message(f'ERROR: {insurance_name} processing failed. Something went wrong.', 'ERROR')

                self.apply_filter(self.billable_claims_filter_name)

    def export_csv(self):
        try_count: int = 0
        success: bool = False
        while try_count <= 3 and not success:
            try:
                common.wait_element(self.browser, "//button[@title='Export']")
                self.browser.click_element_when_visible("//button[@title='Export']")

                common.wait_element(self.browser, "//li/div[contains(.,'Standard Export')]/div/a[text()='CSV']")
                self.browser.click_element_when_visible("//li/div[contains(.,'Standard Export')]/div/a[text()='CSV']")

                # Go to files page
                common.wait_element(self.browser, "//a[text()='Go To Files']")
                self.browser.click_element_when_visible("//a[text()='Go To Files']")
                common.wait_element(self.browser, '//span[text()="File Name"]')
                success = self.browser.does_page_contain_element('//span[text()="File Name"]')
            except Exception as ex:
                common.log_message('export_csv(): ' + str(ex))
                self.apply_filter(self.billable_claims_filter_name)
                time.sleep(5)
            finally:
                try_count += 1
        # Filtering by current employee id
        current_url = self.browser.get_location()
        current_url = current_url + '/?createdByContactId=' + self.employee_id
        self.browser.go_to(current_url)
        common.wait_element(self.browser, f'//em[contains(., "{self.employee_id}")]')
        self.browser.reload_page()

        # Check file name
        file_name = 'Billing from {} to {}'.format(self.start_date.strftime('%m/%d/%Y'), self.end_date.strftime('%m/%d/%Y'))
        common.wait_element_and_refresh(
            browser=self.browser,
            locator="//div[text()='" + datetime.datetime.now().strftime('%m/%d/%Y') + "']/../div/div/a/div[text()='" + file_name + "']",
            timeout=120)
        self.browser.click_element_when_visible(locator="//div[text()='" + datetime.datetime.now().strftime('%m/%d/%Y') + "']/../div/div/a/div[text()='" + file_name + "']")

        # Download file
        common.wait_element(self.browser, '//button[contains(.,"Download")]')
        self.browser.click_element_when_visible('//button[contains(.,"Download")]')

        common.wait_element(self.browser, "//a[contains(@data-bind,'downloadedUrl')]")
        self.browser.click_element_when_visible("//a[contains(@data-bind,'downloadedUrl')]")

    def modifiers_check(self):
        self.apply_filter(self.billable_claims_filter_name)

        if self.is_no_results('No results matched {} filter and date range'.format(self.billable_claims_filter_name)):
            return

        self.export_csv()
        path_to_csv_file = common.get_downloaded_file_path(
            os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'cr'),
            '.csv',
            'Failed to download exported billing report.'
        )
        csv = CsvInterface(path_to_csv_file)
        csv.exported_billing_report_processing()

        if len(csv.different_unique_places) == 0:
            common.log_message('No combination of client ID and procedure code was found that contained multiple records with different unique service locations')
            return

        self.apply_filter(self.billable_claims_filter_name, '&pageSize=100&clientId=1')
        url = self.browser.get_location()

        for client_id, dates_of_service in csv.different_unique_places.items():
            try:
                self.browser.reload_page()
                updated_url = url.replace('&clientId=1', '&clientId=' + client_id)
                self.browser.go_to(updated_url)
                common.wait_element(self.browser, '//em[contains(., "(ID: ' + client_id + ')")]', 45)

                if self.is_no_results('It looks like the record has already been processed'):
                    continue

                headers_index = self.find_header_index(['client', 'date', 'time', 'providers', 'payor', 'service/auth'])
                for date_of_service, procedure_codes in dates_of_service.items():
                    try:
                        self.browser.select_checkbox('//input[@data-bind="checked: listVm.allSelected"]')
                        list_of_providers = []
                        payor = ''

                        rows = self.browser.find_elements("//tbody/tr[contains(@class, 'row-item entry')]")
                        for row in rows:
                            columns = row.find_elements_by_tag_name('td')
                            if columns[headers_index['providers']].text.strip() not in list_of_providers:
                                list_of_providers.append(columns[headers_index['providers']].text.strip())
                                payor = columns[headers_index['payor']].text.strip()

                        location = ''
                        if 'CO Medicaid'.lower() in payor.lower():
                            location = self.get_client_location(client_id, 'CO Medicaid')

                        self.bulk_merge_claims(payor)

                        if not self.prepare_claims_to_generate(payor, client_id, location, list_of_providers):
                            self.browser.click_element_when_visible('//div/ul/li/a[text()="Billing"]')
                            continue

                        # click start claims generation
                        self.start_claims_generation()
                        common.log_message('Claim generated. Client ID: {}'.format(client_id))
                        self.post_claims_generation_and_apply_label(payor)
                    except Exception as ex:
                        common.log_message(str(ex), 'ERROR')
                        common.log_message('Something went wrong. Client ID {}. Date {}'.format(client_id, date_of_service), 'ERROR')
                        self.modifiers_check_error_list_with_id.append(client_id)
            except Exception as ex:
                common.log_message(str(ex), 'ERROR')
                common.log_message('Something went wrong. Client ID {}'.format(client_id), 'ERROR')

    def is_no_results(self, message: str) -> bool:
        common.wait_element(self.browser,
                            '//div[text()="No results matched your keywords, filters, or date range" and not(@style="display: none;")]',
                            timeout=3,
                            is_need_screen=False
                            )
        if self.browser.does_page_contain_element('//div[text()="No results matched your keywords, filters, or date range" and not(@style="display: none;")]'):
            common.log_message(message)
            return True
        return False

    def speech_therapy(self) -> None:
        self.apply_filter(self.billing_scrub_filter_name)

        if self.is_no_results('No results matched {} filter and date range'.format(self.billing_scrub_filter_name)):
            return

        # Open 'Service/Auth' windows
        self.browser.click_element_when_visible("//div/a[text()='Service/Auth']/../../a/i")
        common.wait_element(self.browser, "//div/div/span[text()='servicecodes']/../../div/ul/li")

        all_services = self.browser.find_elements("//div/div/span[text()='servicecodes']/../../div/ul/li")
        count = 0
        for service in all_services:
            if service.text.startswith('92507') or service.text.startswith('92523'):
                count += 1
                service_name = str(service.text)
                print(service_name)
                service.click()
                common.wait_element(self.browser, '//em[text()="Service Code: ' + service_name.split(' ')[
                    0].strip() + ': ' + service_name[service_name.index(' ') + 1:].strip() + '"]')
                self.browser.select_checkbox('//input[@data-bind="checked: listVm.allSelected"]')

                self.bulk_merge_claims()

                self.change_provider_to_all_claims('Provider', 'Katie Repsis')
                self.change_provider_to_all_claims('Provider Supplier', 'Katie Repsis')

                self.start_claims_generation()
                self.post_claims_generation_and_apply_label('')
        if count == 0:
            common.log_message('No service found with 92507 and 92523 codes')

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
        condition = lambda x: str(x).replace('.0', '').strip().lower() == timesheet.cd_number.strip().lower()
        cd_number_first.filter_by_column(self.mapping.fee_schedule_columns_index['CdNum'], condition)
        if len(cd_number_first) == 0:
            raise ValueError('Cd number {} not found in mapping'.format(timesheet.cd_number))

        row_first = None
        if len(cd_number_first) > 1:
            same_row_test = cd_number_first[0]
            index_can_overlap = self.mapping.fee_schedule_columns_index['Can Overlap']
            index_cannot_overlap = self.mapping.fee_schedule_columns_index['Cannot Overlap']
            for row in range(len(cd_number_first)):
                if str(cd_number_first[row][self.mapping.fee_schedule_columns_index['CdDscrpt']]).strip().lower() in \
                        timesheet.service.strip().lower():
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
                'CdNum {} not found in mapping file for payor {}'.format(timesheet.cd_number, fee_schedule_name))
        return row_first

    @staticmethod
    def add_label(timesheets: list, label: str):
        for item in timesheets:
            if label == 'HOLD':
                item.hold_whole_day = True
            if label not in item.labels:
                item.labels.append(label)

    @staticmethod
    def identify_overlap_label(key_timesheet: Timesheet, grouped_timesheet: Timesheet):
        lover_rate = grouped_timesheet
        if key_timesheet.rate < grouped_timesheet.rate:
            lover_rate = key_timesheet
        elif key_timesheet.rate == grouped_timesheet.rate and key_timesheet.charges < grouped_timesheet.charges:
            lover_rate = key_timesheet
        if 'OVERLAP' not in lover_rate.labels:
            lover_rate.labels.append('OVERLAP')
        if 'HOLD' not in lover_rate.labels:
            lover_rate.labels.append('HOLD')

    def check_2_to_1(self, key_timesheet: Timesheet, payor: str, fee_schedule_name: str) -> bool:
        # Check SCA sheet - 2 to 1 okay
        if key_timesheet.client_id.lower() in self.mapping.sca and \
                (payor.lower() in self.mapping.sca.values() or fee_schedule_name.lower() in self.mapping.sca.values()):
            return True
        return False

    def is_valid_provider_tag(self, timesheet: Timesheet, tag: str) -> bool:
        try:
            browser_tabs = self.browser.get_window_handles()
            self.browser.switch_window(browser_tabs[1])

            self.apply_filter(self.billing_scrub_filter_name, f'&billingEntryId={timesheet.timesheet_id}')
            common.wait_element(self.browser, f'//em[contains(., "{timesheet.timesheet_id}")]')

            provider_id: str = self.browser.get_element_attribute(f'//tr[@id="billing-grid-row-{timesheet.timesheet_id}"]//a[@data-title="Click to filter by this provider"]/../a[2]', 'contactid')

            self.browser.scroll_element_into_view('//a[@contactid="' + provider_id + '"]')
            self.browser.click_element_when_visible('//a[@contactid="' + provider_id + '"]')
            common.wait_element(self.browser, '//small[text()="Upload File"]')
            common.wait_element(self.browser, '//a[text()=" Labels"]', timeout=10, is_need_screen=False)
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

    def verify_overlap(self, timesheets: list):
        overlaped: dict = self.grouping_of_overlap(timesheets)

        for key_timesheet, grouped_timesheets in overlaped.items():
            try:
                payor = str(key_timesheet.payor).strip()
                # Check if payor exist in mapping file
                if payor.lower() not in self.mapping.payor_mapping:
                    raise ValueError('Payor {} not found in mapping'.format(payor))

                # Check if fee schedule name exist in mapping file and filter table
                fee_schedule_name = str(self.mapping.payor_mapping[payor.lower()]).strip()
                # CR from customer
                if fee_schedule_name.lower() == 'Managed Health Network'.lower() and key_timesheet.cd_number == '96152':
                    self.add_label(timesheets, 'HOLD')

                condition = lambda x: str(x).strip().lower() == fee_schedule_name.lower()
                temp_table = self.mapping.fee_schedule_table.copy()
                temp_table.filter_by_column(self.mapping.fee_schedule_columns_index['FeeSched'], condition)
                if len(temp_table) == 0:
                    raise ValueError('Fee schedule not contain {} value'.format(fee_schedule_name))
                row_key = self.validate_cd_number(temp_table, key_timesheet, fee_schedule_name)
                number_key = key_timesheet.cd_number.lower()
                can_key = str(row_key[self.mapping.fee_schedule_columns_index['Can Overlap']]).strip().lower()
                for grouped_timesheet in grouped_timesheets:
                    # Validate cd numbers
                    # Change request from customer
                    if fee_schedule_name.lower() == 'Managed Health Network'.lower() and grouped_timesheet.cd_number == '96152':
                        self.add_label(timesheets, 'HOLD')
                    row_grouped = self.validate_cd_number(temp_table, grouped_timesheet, fee_schedule_name)
                    number_grouped = grouped_timesheet.cd_number.lower()

                    can_grouped = str(row_grouped[self.mapping.fee_schedule_columns_index['Can Overlap']]).strip().lower()

                    # check if overlap permitted
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
                    self.identify_overlap_label(key_timesheet, grouped_timesheet)
                    if fee_schedule_name.lower() != 'Tricare West'.lower():
                        self.add_label(timesheets, 'HOLD')
                    Timesheet.overlap[key_timesheet.client] = timesheets.copy()
            except Exception as ex:
                common.log_message('ERROR:   {}'.format(str(ex)), 'ERROR')
                common.log_message(str(key_timesheet), 'ERROR')
                for grouped_timesheet in grouped_timesheets:
                    print(grouped_timesheet)

    def apply_label_processing(self, url: str, timesheets: list, headers_index: dict):
        self.browser.reload_page()
        client_id = timesheets[0].client_id
        updated_url = url + '&clientId=' + client_id
        self.browser.go_to(updated_url)
        common.wait_element(self.browser, '//em[contains(., "(ID: ' + client_id + ')")]')
        common.wait_element(self.browser, '//input[@data-bind="checked: listVm.allSelected"]')

        # Apply OVERLAP
        rows = self.browser.find_elements("//tbody/tr[contains(@class, 'row-item entry')]")
        elem = self.browser.find_elements('//input[@class="select-entry"]')
        count = 0
        for item in timesheets:
            for row in rows:
                columns = row.find_elements_by_tag_name('td')
                if columns[headers_index['time']].text.strip() == item.time and 'OVERLAP' in item.labels and \
                        item.cd_number.lower() in columns[headers_index['service/auth']].text.lower() and \
                        item.service.lower() in columns[headers_index['service/auth']].text.lower() and \
                        item.charges == round(float('0' + str(columns[headers_index['charges_agreed']].text)), 2):
                    count += 1
                    elem[rows.index(row)].click()
                    break
        if count > 0:
            self.apply_label('OVERLAP', '')

        # If whole day impacted
        if timesheets[0].hold_whole_day:
            # Apply HOLD and remove Ready to bill
            common.wait_element(self.browser, '//input[@data-bind="checked: listVm.allSelected"]')
            self.browser.select_checkbox('//input[@data-bind="checked: listVm.allSelected"]')
            self.apply_label('HOLD', 'Ready to bill')
        else:
            common.wait_element(self.browser, '//input[@data-bind="checked: listVm.allSelected"]')
            self.browser.select_checkbox('//input[@data-bind="checked: listVm.allSelected"]')
            self.browser.unselect_checkbox('//input[@data-bind="checked: listVm.allSelected"]')
            count = 0
            for item in timesheets:
                for row in rows:
                    columns = row.find_elements_by_tag_name('td')
                    if columns[headers_index['time']].text.strip() == item.time and 'HOLD' in item.labels and \
                            item.cd_number.lower() in columns[headers_index['service/auth']].text.lower() and \
                            item.service.lower() in columns[headers_index['service/auth']].text.lower() and \
                            item.charges == round(float('0' + str(columns[headers_index['charges_agreed']].text)), 2):
                        count += 1
                        elem[rows.index(row)].click()
                        break
            if count > 0:
                self.apply_label('HOLD', 'Ready to bill')

    def overlap_check(self):
        self.apply_filter(self.billing_scrub_filter_name, '&isOverlapping=2&pageSize=750', True)
        common.wait_element(self.browser, "//em[text()='Overlapping: By client']")

        if self.is_no_results('No overlaps'):
            return

        headers_index = self.find_header_index(['client', 'date', 'time', 'payor', 'service/auth', 'agreed'])
        rows = self.browser.find_elements("//tbody/tr[contains(@class, 'row-item entry')]")
        common.log_message('Found {} filtered rows'.format(len(rows)))
        last_user_id = ''
        timesheets = []

        for row in rows:
            columns = row.find_elements_by_tag_name('td')

            tmp = {}
            for header, index in headers_index.items():
                if header not in tmp:
                    tmp[header] = str(columns[index].text)

            if self.does_need_skip_insurance(tmp['payor'].strip()):
                continue

            tmp_col = columns[headers_index['client']].find_elements_by_tag_name('a')
            client_id = tmp_col[1].get_attribute('contactid')

            timesheet_id: str = row.get_attribute('id').split('-')[-1]
            if (len(last_user_id) > 0 and last_user_id != client_id) or rows.index(row) == len(rows) - 1:
                if rows.index(row) == len(rows) - 1:
                    try:
                        timesheets.append(
                            Timesheet(timesheet_id, tmp['client'], tmp['date'], tmp['time'], tmp['payor'],
                                      tmp['service/auth'], tmp['agreed'], tmp['charges_agreed'], client_id)
                        )
                    except Exception as e:
                        common.log_message(
                            'Parsing error. Timesheet data: {}'.format(str.join(', ', list(tmp.values()))))
                        common.log_message(str(e))
                self.verify_overlap(timesheets)
                timesheets.clear()
            try:
                timesheets.append(
                    Timesheet(timesheet_id, tmp['client'], tmp['date'], tmp['time'], tmp['payor'],
                              tmp['service/auth'], tmp['agreed'], tmp['charges_agreed'], client_id))
            except Exception as e:
                common.log_message('Parsing error. Timesheet data: {}'.format(str.join(', ', list(tmp.values()))))
                common.log_message(str(e))
            last_user_id = client_id

        if len(Timesheet.overlap) > 0:
            common.log_message('Found {} clients with not permitted overlap'.format(len(Timesheet.overlap)))

            self.apply_filter(self.billing_scrub_filter_name, '&pageSize=100&clientId=1')
            url = self.browser.get_location()
            url = url.replace('&clientId=1', '')

            for key, value in Timesheet.overlap.items():
                try:
                    self.apply_label_processing(url, value, headers_index)
                except Exception as e:
                    common.log_message('Something went wrong when bot apply label to {}'.format(key), 'ERROR')
                    common.log_message(str(e), 'ERROR')
                    self.browser.capture_page_screenshot(
                        os.path.join(
                            os.environ.get("ROBOT_ROOT", os.getcwd()),
                            'output',
                            'Something_went_wrong_{}.png'.format(str(key).replace('"', '').replace("'", ""))
                        )
                    )
        else:
            common.log_message('No overlaps')
