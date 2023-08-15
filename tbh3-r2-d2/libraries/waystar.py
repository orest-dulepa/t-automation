from RPA.Browser.Selenium import Selenium
import fitz
from libraries import common
from urllib.parse import urlparse
import datetime
import time
import os
import shutil
import re


class WayStar:

    def __init__(self, credentials: dict):
        self.credentials: dict = credentials
        self.browser: Selenium = Selenium()
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.base_url: str = self.get_base_url()
        self.path_to_temp: str = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'waystar')
        self.login_to_site()
        self.start_url: str = self.browser.get_location()

    def get_base_url(self):
        parsed_uri = urlparse(self.url)
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

    def login_to_site(self):
        self.browser.close_browser()
        self.browser.timeout = 45
        self.is_site_available = False
        count = 1

        if os.path.exists(self.path_to_temp):
            shutil.rmtree(self.path_to_temp)
        os.mkdir(self.path_to_temp)
        self.browser.set_download_directory(self.path_to_temp, True)

        while count < 2 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.url)
                self.browser.set_window_size(1920, 1080)
                self.browser.maximize_browser_window()
                common.wait_element(self.browser, '//input[@type="password"]', is_need_screen=False)
                self.browser.input_text_when_element_is_visible('//input[@type="text"]', self.login)
                self.browser.input_text_when_element_is_visible('//input[@type="password"]', self.password)
                self.browser.click_button_when_visible('//input[@id="loginButton"]')

                if self.browser.does_page_contain_element('//h1[text()="Login failed"]'):
                    elem = self.browser.find_element('//h1[text()="Login failed"]')
                    if elem.is_displayed():
                        raise Exception('Logging into WayStar failed')

                common.wait_element_and_refresh(self.browser, '//h1[contains(., "Professional Claims")]', 5, is_need_screen=False)
                if self.browser.does_page_contain_element('//h2[text()="Additional Authentication Required"]'):
                    question: str = str(self.browser.get_text('//strong')).strip()
                    if question in self.credentials:
                        self.browser.input_text_when_element_is_visible('//input[@id="verifyAnswer"]', self.credentials[question])
                        self.browser.click_element_when_visible('//input[@id="VerifyButton"]')
                        common.wait_element_and_refresh(self.browser, '//h1[contains(., "Professional Claims")]', 5, is_need_screen=False)

                while self.browser.does_page_contain_element('//button[contains(@onclick, "alert")]'):
                    self.browser.click_element_when_visible('//button[contains(@onclick, "alert")]')
                    common.wait_element_and_refresh(self.browser, '//h1[contains(., "Professional Claims")]', 3, is_need_screen=False)

                self.is_site_available = self.browser.does_page_contain_element('//h1[contains(., "Professional Claims")]')
            except Exception as ex:
                common.log_message("Logging into WayStar. Attempt #{} failed".format(count), 'ERROR')
                common.log_message(str(ex))
                self.browser.capture_page_screenshot(
                    os.path.join(
                        os.environ.get("ROBOT_ROOT", os.getcwd()),
                        'output',
                        f'WayStar_login_failed_{count}.png'
                    )
                )
                self.browser.close_browser()
            finally:
                count += 1
                if not self.is_site_available:
                    self.browser.capture_page_screenshot(
                        os.path.join(
                            os.environ.get("ROBOT_ROOT", os.getcwd()),
                            'output',
                            f'WayStar_login_failed.png'
                        )
                    )

    @staticmethod
    def get_service_info(eob_data: dict, service_code: str, amount: str) -> dict:
        if service_code not in eob_data['services']:
            return {}
        for item in eob_data['services'][service_code]:
            if item['billed'] == amount:
                return item
        return {}

    @staticmethod
    def get_index(line_from_pdf: str, search_word: str) -> int:
        temp_array: list = line_from_pdf.split('\n')
        for item in temp_array:
            if search_word in item:
                return temp_array.index(item)
        return -1

    def read_remit_file(self) -> str:
        path_to_pdf: str = common.get_downloaded_file_path(self.path_to_temp, '.pdf', 'Cannot download Remit file')

        text: str = ""
        with fitz.Document(path_to_pdf) as doc:
            for page in doc:
                text += page.getText()
        os.remove(path_to_pdf)

        return text

    @staticmethod
    def add_if_unique(eob_data: dict, service: str, data: dict):
        if service not in eob_data:
            eob_data[service] = []

        for item in eob_data[service]:
            if item['billed'] == data['billed'] and item['obligation_code'] == data['obligation_code'] \
                    and item['allowed'] == data['allowed'] and item['obligation_amount'] == data['obligation_amount']:
                return
        eob_data[service].append(data)

    def parse_remit_file(self, eob_data: dict, date_of_service_str: str):
        text: str = self.read_remit_file()
        text_array: list = text.split('\n')

        for i in range(len(text_array)):
            line: str = str(text_array[i]).strip()

            if date_of_service_str in line:
                new_position: int = i + 1
                while len(str(text_array[new_position]).strip()) != 5:
                    new_position += 1
                service: str = str(text_array[new_position]).strip().upper()

                check_mod = re.search(r'\d+\.\d{2}', str(text_array[new_position + 1]).strip())
                if check_mod is None:
                    new_position += 1

                allowed: str = ''
                billed: str = ''
                prov_pd: str = ''
                obligation_amount: str = '0.0'
                count: int = 0
                while True:
                    new_position += 1
                    if date_of_service_str in str(text_array[new_position]).strip() or new_position + 1 == len(text_array):
                        self.add_if_unique(eob_data, service, {
                            'billed': round(float(billed), 2),
                            'allowed': round(float(allowed), 2),
                            'obligation_code': '',
                            'obligation_amount': round(float(obligation_amount), 2),
                            'prov_pd': round(float(prov_pd), 2),
                        })
                        break

                    check_amount = re.search(r'\d+\.\d{2}', str(text_array[new_position]).strip())
                    if check_amount is None:
                        obligation_code = str(text_array[new_position]).strip().upper()
                        if re.search(r'PR-\d', obligation_code) is not None:
                            obligation_amount: str = str(text_array[new_position + 1]).upper()
                            if not prov_pd:
                                prov_pd = str(text_array[new_position + 2]).strip().upper()
                            self.add_if_unique(eob_data, service, {
                                'billed': round(float(billed), 2),
                                'allowed': round(float(allowed), 2),
                                'obligation_code': obligation_code,
                                'obligation_amount': round(float(obligation_amount), 2),
                                'prov_pd': round(float(prov_pd), 2),
                            })
                            break
                        continue

                    count += 1
                    if count == 1:
                        billed = str(text_array[new_position]).strip()

                        check_billed: list = billed.split()
                        if len(check_billed) == 2:
                            billed = check_billed[0]
                            allowed = check_billed[1]
                            count += 1
                        elif len(check_billed) == 3:
                            billed = check_billed[0]
                            allowed = check_billed[1]
                            count += 2
                    elif count == 2:
                        allowed = str(text_array[new_position]).strip()

                        check_allowed: list = allowed.split()
                        if len(check_allowed) == 2:
                            allowed = check_allowed[0]
                            count += 1
                        elif len(check_allowed) == 3:
                            allowed = check_allowed[0]
                            obligation_amount = check_allowed[2]
                            count += 2
                    elif count == 3:
                        check_3: list = str(text_array[new_position]).strip().split()
                        if len(check_3) == 2:
                            obligation_amount = check_3[1]
                            count += 1
                    elif count == 4 and 'Patient Responsibility' in text:
                        obligation_amount = str(text_array[new_position]).strip()
                    elif count == 5:
                        check_5: list = str(text_array[new_position]).strip().split()
                        if len(check_5) == 2:
                            prov_pd = check_5[1]
                            count += 1
                    elif count == 6:
                        prov_pd = str(text_array[new_position]).strip()
                        check_prov_pd: list = prov_pd.split()
                        if len(check_prov_pd) == 2:
                            prov_pd = check_prov_pd[0]

    def download_and_parse_remit_file(self, date_of_service: datetime) -> dict:
        eob_data: dict = {}

        try:
            count_of_files = len(self.browser.find_elements('//span[@title="Has Remit"]'))
        except:
            time.sleep(2)
            count_of_files = len(self.browser.find_elements('//span[@title="Has Remit"]'))

        date_of_service_str: str = date_of_service.strftime('%m%d%y')
        for n in range(1, count_of_files + 1):
            try:
                tab = self.browser.get_window_handles()
                self.browser.switch_window(tab[0])

                self.browser.click_element_when_visible(f'(//span[@title="Has Remit"])[{n}]')
                try:
                    tab = self.browser.get_window_handles()
                    self.browser.switch_window(tab[-1])

                    path_to_pdf: str = common.get_downloaded_file_path(self.path_to_temp, '.pdf')

                    if path_to_pdf:
                        self.parse_remit_file(eob_data, date_of_service_str)
                    elif self.browser.does_page_contain_element('//a[text()="EOB"]'):
                        count: int = len(self.browser.find_elements('//a[text()="EOB"]'))
                        for i in range(1, count + 1):
                            self.browser.click_element_when_visible(f'(//a[text()="EOB"])[{i}]')
                            self.parse_remit_file(eob_data, date_of_service_str)
                except Exception as download_error:
                    if 'Cannot download Remit file' in str(download_error):
                        raise Exception
                    elif 'Timed out receiving message from renderer' in str(download_error):
                        self.parse_remit_file(eob_data, date_of_service_str)
                    common.log_message(f'OEB download: {str(download_error)}')
                finally:
                    tab = self.browser.get_window_handles()
                    self.browser.switch_window(tab[-1])
                    self.browser.close_window()
                    self.browser.switch_window(tab[0])
            except Exception as error:
                common.log_message(f'OEB: {str(error)}')
        return eob_data

    def select_date(self, date_of_service: datetime):
        common.wait_element(self.browser, '//div[@id="ui-datepicker-div"]')
        self.browser.select_from_list_by_value('//div[@id="ui-datepicker-div"]//select[@data-handler="selectMonth"]', str(date_of_service.month - 1))
        self.browser.select_from_list_by_value('//div[@id="ui-datepicker-div"]//select[@data-handler="selectYear"]', str(date_of_service.year))
        self.browser.click_element_when_visible(f'//div[@id="ui-datepicker-div"]//a[text()="{date_of_service.day}"]')
        self.browser.wait_until_element_is_not_visible('//div[@id="ui-datepicker-div"]')

    def search_by_client(self, client_name: str, date_of_service: datetime, claim_id: str = ''):
        tab = self.browser.get_window_handles()
        self.browser.switch_window(tab[0])

        self.browser.go_to(self.start_url)

        common.wait_element(self.browser, '//select[@id="SearchCriteria_Status"]')
        self.browser.select_from_list_by_value('//select[@id="SearchCriteria_Status"]', '-1')
        self.browser.input_text_when_element_is_visible('//input[@id="SearchCriteria_PatientNames"]', client_name)

        self.browser.select_from_list_by_value('//select[@id="SearchCriteria_ServiceDate"]', 'Custom')
        common.wait_element(self.browser, '//input[@id="serviceDateFromDateBox"]')

        self.browser.click_element_when_visible('//input[@id="serviceDateFromDateBox"]')
        self.select_date(date_of_service)

        self.browser.click_element_when_visible('//input[@id="serviceDateToDateBox"]')
        self.select_date(date_of_service)

        self.browser.select_from_list_by_value('//select[@id="SearchCriteria_TransDate"]', '2 years')

        self.browser.click_element_when_visible('//input[@id="ClaimListingSearchButtonBottom"]')
        common.click_and_wait(self.browser, '//input[@id="ClaimListingSearchButtonBottom"]', f'//td[contains(@class, "patientNumberCell") and contains(.,"{ claim_id }")]')
        self.browser.wait_until_element_is_not_visible('//div[@id="progressBackgroundFilter"]')

    def close_not_used_window(self):
        tab = self.browser.get_window_handles()
        for i in range(len(tab) - 1, 0, -1):
            try:
                self.browser.switch_window(tab[i])
                self.browser.close_window()
            except:
                pass

        tab = self.browser.get_window_handles()
        self.browser.switch_window(tab[0])

    def get_eob_data(self, client_name: str, date_of_service: datetime, claim_id: str = '') -> dict:
        self.close_not_used_window()

        client_name_new: str = client_name
        if len(client_name.split()) > 2:
            client_name_new: str = client_name.split()[0] + ' ' + client_name.split()[-1]
        self.search_by_client(client_name_new, date_of_service, claim_id)
        if not self.browser.does_page_contain_element('//span[@title="Has Remit"]'):
            common.log_message('ERROR: EOB button does not exist', 'ERROR')
            return {}

        eob_data: dict = self.download_and_parse_remit_file(date_of_service)
        self.close_not_used_window()

        return eob_data
