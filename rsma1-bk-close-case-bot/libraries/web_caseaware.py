import time

from RPA.Browser.Selenium import Selenium
from libraries import common as com
import os


class CaseAware:
    def __init__(self, credentials: dict, is_test_run: bool = False):
        self.test_run: bool = is_test_run
        self.is_failed: bool = False
        self.error_message: str = ''
        self.browser: Selenium = Selenium()
        self.credentials: dict = credentials
        self.is_site_available: bool = False
        self.email_exception = []
        self.file_found = False
        root_path = os.environ.get("ROBOT_ROOT", os.getcwd())
        self.path_to_temp = os.path.join(root_path, 'temp')
        self.cases_to_process = []
        self.any_task = False
        self.can_close_case = False

    def open_login(self):
        preferences = {
            'download.default_directory': self.path_to_temp,
            'plugins.always_open_pdf_externally': True,
            'download.directory_upgrade': True,
            'download.prompt_for_download': False
        }
        count = 1
        while count <= 3 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.credentials['url'], preferences=preferences)
                self.browser.set_window_size(1920, 1080)
                if not self.browser.does_page_contain_element("//input[@name='usr']"):
                    if not self.browser.find_element("//input[@name='usr']").is_displayed():
                        com.log_message("Logging into CaseAware failed. Input field not found.", 'ERROR')
                        self.browser.capture_page_screenshot(
                            os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output',
                                         f'CaseAware_login_fail_{count}.png'))
                        return
                self.browser.input_text_when_element_is_visible("//input[@name='usr']", self.credentials['login'])
                self.browser.input_text_when_element_is_visible("//input[@name='pwd']", self.credentials['password'])
                self.browser.click_element_when_visible("//a[text()='Login']")
                com.wait_element(self.browser, '//b[text()="Welcome to the CaseAware® System!"]')
                self.is_site_available = self.browser.does_page_contain_element("//a[text()='Find File']")
            except Exception as ex:
                com.log_message(f"Logging into CaseAware. Attempt #{count} failed", 'ERROR')
                print(str(ex))
                self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output',
                                                                  f'CaseAware_login_fail_{count}.png'))
                self.browser.close_browser()
            finally:
                count += 1

    def get_tasks(self):
        self.browser.mouse_over('//a[text()="Files"]')
        self.browser.click_element_when_visible('//a[text()="Current Steps"]')
        com.wait_element(self.browser, '//a[contains(text(), "(Bankruptcy)")]')
        loan_numbers = self.browser.find_elements('//td[a[contains(text(), "(Bankruptcy)")]]/following-sibling::td[2]')
        case_numbers = self.browser.find_elements('//a[contains(text(), "(Bankruptcy)")]')
        steps_column = self.browser.find_elements('//td[a[contains(text(), "(Bankruptcy)")]]/following-sibling::td[4]')
        counter = 0
        total_num = len(steps_column)
        while counter < total_num:
            if '2510' in steps_column[counter].text:
                self.cases_to_process.append({'case_number': case_numbers[counter].text.split(' ')[0],
                                              'loan_number': loan_numbers[counter].text})
            counter += 1
        if len(self.cases_to_process) > 0:
            self.any_task = True
            self.browser.click_element_when_visible('//a[text()="Home"]')
            return
        else:
            com.log_message("No 2510 tasks to process")
            exit(1)

    def close_logout(self):
        self.browser.click_element_when_visible('//li[@class="has-sub"]/a[contains(text(), ", ")]')
        com.wait_element(self.browser, '//li[@class="has-sub"]/ul/li/a[text()="Logout"]')
        self.browser.click_element_when_visible('//li[@class="has-sub"]/ul/li/a[text()="Logout"]')
        self.browser.handle_alert()
        self.browser.close_window()
        print('Logged out')

    def navigate_to_case(self, case_number: str):
        com.wait_element(self.browser, '//a[text()="Home"]')
        self.browser.click_element_when_visible('//a[text()="Home"]')
        com.wait_element(self.browser, '//input[@name="filt_cnum" and @type="text"]')
        self.browser.input_text_when_element_is_visible('//input[@name="filt_cnum" and @type="text"]', case_number)
        com.wait_element(self.browser, '//a[@class="button" and text()="Find Case"]')
        self.browser.click_element_when_visible('//a[@class="button" and text()="Find Case"]')
        com.wait_element(self.browser, '//a[contains(., "View Case")]')

    def is_task_completed(self) -> bool:
        com.wait_element(self.browser, '//div[@id="lst_grid_dtls_div"]')
        desc_cols = self.browser.find_elements('//div[@id="lst_grid_dtls_div"]//tr/td[1]')
        date_cols = self.browser.find_elements('//div[@id="lst_grid_dtls_div"]//tr/td[6]')
        i = 0
        skip = 0
        while True:
            if desc_cols[i+skip].get_attribute('align') != 'left':
                skip += 1
                continue
            if '200. Notice' in desc_cols[i+skip].text:
                if date_cols[i].text != "Today":
                    return True
            i += 1
            if i+skip < len(desc_cols):
                continue
            else:
                break
        return False

    def navigate_to_fees(self):
        try:
            com.wait_element(self.browser, '//table[contains(@id, "tabs_row_1")]//a[contains(., "Fees/Payables")]')
            self.browser.click_element_when_visible('//table[contains(@id, "tabs_row_1")]//a[contains(., "Fees/Payables")]')
        except:
            com.wait_element(self.browser, '//a[contains(text(), "More") and contains(@id, "tabs_row_1_link")]')
            self.browser.click_element_when_visible('//a[contains(text(), "More") and contains(@id, "tabs_row_1_link")]')
            com.wait_element(self.browser, '//ul[contains(@id, "tabs_row_1_ul")]//a[contains(., "Fees/Payables")]')
            self.browser.click_element_when_visible('//ul[contains(@id, "tabs_row_1_ul")]//a[contains(., "Fees/Payables")]')
        com.wait_element(self.browser, '//td[contains(text(), "Case Charges")]')
        el = self.browser.find_elements('//table[@id="lst_grid_dtls_tbl"]/tbody/tr[td[contains(., "Fee - Attorney Fee")]]')
        if len(el) > 0:
            self.can_close_case = True

    def close_case(self):
        com.wait_element(self.browser, '//a[contains(., "Edit Case")]')
        self.browser.click_element_when_visible('//a[contains(., "Edit Case")]')
        com.wait_element(self.browser, '//div[contains(text(), "Cases Edit")]')
        self.browser.select_from_list_by_value('//select[@id="cur_case_stat_id"]', str(3))
        self.browser.click_element_when_visible('//a[text()="Save" and @class="button"]')
        time.sleep(1)
        self.browser.switch_window(self.browser.get_window_handles()[1])
        com.wait_element(self.browser, '//select[@id="close_id"]')
        self.browser.select_from_list_by_value('//select[@id="close_id"]', str(32))
        com.wait_element(self.browser, '//textarea[@id="notes"]')
        self.browser.input_text_when_element_is_visible('//textarea[@id="notes"]', 'NOPC Filed')
        self.browser.click_element_when_visible('//a[text()="Save" and @class="button"]')
        self.browser.switch_window(self.browser.get_window_handles()[0])
        time.sleep(5)
        self.browser.click_element_when_visible('//a[text()="Home"]')
