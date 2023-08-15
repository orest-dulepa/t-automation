from RPA.Browser.Selenium import Selenium
from libraries import common
from urllib.parse import urlparse
import datetime
import time
import os
import shutil
from libraries.pdf import PDF
from libraries.eob import EOB


class WayStar:

    def __init__(self, credentials: dict):
        self.credentials: dict = credentials
        self.browser: Selenium = Selenium()
        self.browser.timeout = 60
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.base_url: str = self.get_base_url()
        self.path_to_temp: str = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'waystar')
        self.login_to_site()
        self.start_url: str = self.browser.get_location()

    def get_base_url(self) -> str:
        parsed_uri = urlparse(self.url)
        base_url: str = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

    def login_to_site(self):
        self.browser.close_browser()
        self.is_site_available = False
        count: int = 1

        if os.path.exists(self.path_to_temp):
            shutil.rmtree(self.path_to_temp)
        os.mkdir(self.path_to_temp)
        self.browser.set_download_directory(self.path_to_temp, True)

        while count < 4 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.url, headless=True)
                self.browser.set_window_size(1920, 1080)
                self.browser.maximize_browser_window()
                self.wait_element('//input[@type="password"]', is_need_screen=False)
                self.browser.input_text_when_element_is_visible('//input[@type="text"]', self.login)
                self.browser.input_text_when_element_is_visible('//input[@type="password"]', self.password)
                self.browser.click_button_when_visible('//input[@id="loginButton"]')

                if self.browser.does_page_contain_element('//h1[text()="Login failed"]'):
                    elem = self.browser.find_element('//h1[text()="Login failed"]')
                    if elem.is_displayed():
                        raise Exception('Logging into WayStar failed')

                self.wait_element('//h1[contains(., "Professional Claims")]', 5, is_need_screen=False)
                if self.browser.does_page_contain_element('//h2[text()="Additional Authentication Required"]'):
                    question: str = str(self.browser.get_text('//strong')).strip()
                    if question in self.credentials:
                        self.browser.input_text_when_element_is_visible('//input[@id="verifyAnswer"]', self.credentials[question])
                        self.browser.click_element_when_visible('//input[@id="VerifyButton"]')
                        self.wait_element('//h1[contains(., "Professional Claims")]', 5, is_need_screen=False)

                while self.browser.does_page_contain_element('//button[contains(@onclick, "alert")]'):
                    self.browser.click_element_when_visible('//button[contains(@onclick, "alert")]')
                    self.wait_element('//h1[contains(., "Professional Claims")]', 3, is_need_screen=False)

                self.is_site_available = self.browser.does_page_contain_element('//a[text()="My Work"]')
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

    def wait_element(self, xpath: str, timeout: int = 60, is_need_screen: bool = True) -> None:
        is_success: bool = False
        timer: datetime = datetime.datetime.now() + datetime.timedelta(0, timeout)

        while not is_success and timer > datetime.datetime.now():
            self.close_specific_windows('//span[text()="Error"]/../a[@role="button"]')

            time.sleep(1)
            if self.browser.does_page_contain_element(xpath):
                try:
                    is_success = self.browser.find_element(xpath).is_displayed()
                except:
                    time.sleep(1)
        if not is_success and is_need_screen:
            common.log_message('Element \'{}\' not available'.format(xpath), 'ERROR')
            self.browser.capture_page_screenshot(
                os.path.join(os.environ.get(
                    "ROBOT_ROOT", os.getcwd()),
                    'output',
                    'Element_not_available_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
                )
            )

    def wait_and_click(self, xpath: str, timeout: int = 60) -> None:
        self.wait_element(xpath, timeout)
        self.browser.click_element_when_visible(xpath)

    def navigate_to_payments_page(self) -> None:
        self.browser.reload_page()
        self.wait_and_click('//a[text()="Claims Processing"]')
        self.wait_and_click('//a[text()="Remits"]')
        self.wait_and_click('//div[@class="link-panel"]/a[text()="Payments"]')
        self.wait_element('//li[@class="selected"]/a[text()="Payments"]')

        # Select View Options -> All
        self.wait_and_click('//span[text()="View Options"]/../following-sibling::li[1]/div/div')
        self.wait_and_click('//span[text()="View Options"]/../following-sibling::li[1]/div/ul/li[text()="All"]')

    def get_downloaded_file_path(self, extension: str, error_message: str = '') -> str:
        downloaded_files: list = []
        timer: datetime = datetime.datetime.now() + datetime.timedelta(0, 60 * 1)

        while timer > datetime.datetime.now():
            time.sleep(1)
            downloaded_files: list = [f for f in os.listdir(self.path_to_temp) if os.path.isfile(os.path.join(self.path_to_temp, f))]
            if downloaded_files and downloaded_files[0].endswith(extension):
                break
        if not downloaded_files:
            if error_message:
                raise Exception(error_message)
            return ''
        file_path = os.path.join(self.path_to_temp, downloaded_files[0])
        return file_path

    def search_payment_and_download_eob(self, check_number: str) -> str:
        self.browser.input_text_when_element_is_visible('//input[@id="txtPaymentNumber"]', check_number)
        self.browser.click_element_when_visible('//input[@name="btnSearch"]')

        self.wait_element(f'//span[text()="{check_number}"]', is_need_screen=False)
        if not self.browser.does_page_contain_element('//a[@data-gaevent="PaymentsRowEOBClick"]'):
            return ''
        self.browser.click_element_when_visible('//a[@data-gaevent="PaymentsRowEOBClick"]')

        self.wait_element('//span[text()="popout"]/..')
        if not self.browser.does_page_contain_element('//span[text()="popout"]/..'):
            return ''
        if os.path.exists(self.path_to_temp):
            shutil.rmtree(self.path_to_temp)
        os.mkdir(self.path_to_temp)
        self.browser.click_element_when_visible('//span[text()="popout"]/..')

        path_to_remit_file: str = self.get_downloaded_file_path('.pdf', '')
        return path_to_remit_file

    def get_payment_eob(self, check_number: str) -> (EOB, dict):
        self.navigate_to_payments_page()
        path_to_eob_file: str = self.search_payment_and_download_eob(check_number)
        if not path_to_eob_file:
            common.log_message(f'Unable to download EOB from the Waystar for {check_number}')

        eob_data: EOB = EOB()
        acnt_data: dict = {}
        if not path_to_eob_file:
            return eob_data, acnt_data

        pdf: PDF = PDF()
        eob_data, acnt_data = pdf.parse_eob(path_to_eob_file)
        return eob_data, acnt_data

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
