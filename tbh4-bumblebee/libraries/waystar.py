from RPA.Browser.Selenium import Selenium
from selenium.webdriver.common.keys import Keys

from libraries import common as com
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
        self.browser.timeout = 45
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.base_url: str = self.get_base_url()
        self.path_to_temp: str = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'waystar')
        self.testMode = True

    # ============================TEST====================================================

    def dev_attach_browser(self):
        self.browser.attach_chrome_browser(1234)
        if self.browser.does_page_contain_element('//*[@id="waystarHeader"]'):
            print("browser was attached")

    # ============================TEST====================================================

    def get_base_url(self) -> str:
        parsed_uri = urlparse(self.url)
        base_url: str = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

    def close_browser(self):
        self.browser.close_browser()

    def login_to_site(self):
        self.browser.close_browser()
        self.is_site_available = False
        count: int = 1

        if os.path.exists(self.path_to_temp):
            shutil.rmtree(self.path_to_temp)
        os.mkdir(self.path_to_temp)
        self.browser.set_download_directory(self.path_to_temp, True)

        while count < 2 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.url)
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

                self.is_site_available = self.browser.does_page_contain_element('//h1[contains(., "Professional Claims")]')
            except Exception as ex:
                com.log_message("Logging into WayStar. Attempt #{} failed".format(count), 'ERROR')
                com.log_message(str(ex))
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

    def wait_element(self, xpath: str, timeout: int = 60, is_need_screen: bool = True) -> None:
        is_success: bool = False
        timer: datetime = datetime.datetime.now() + datetime.timedelta(0, timeout)

        while not is_success and timer > datetime.datetime.now():

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
            com.log_message('Element \'{}\' not available'.format(xpath), 'ERROR')
            self.browser.capture_page_screenshot(
                os.path.join(os.environ.get(
                    "ROBOT_ROOT", os.getcwd()),
                    'output',
                    'Element_not_available_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
                )
            )

    def wait_and_click(self, xpath: str) -> None:
        self.wait_element(xpath)
        self.browser.click_element_when_visible(xpath)

    def navigate_to_batches_page(self) -> None:
        try:
            if not self.is_element_available('//a[text()="Patient Tools"]', 30):
                self.additional_authentication_required()
                self.pass_alerts()

            self.wait_and_click('//a[text()="Patient Tools"]')
            self.wait_and_click('//a[text()="Print Services"]')
            self.wait_and_click('//div[@class="link-panel"]/a[text()="Batches"]')
            self.wait_element('//input[@id="btnUpload"]')
        except Exception as ex:
            raise Exception("Error navigate to batches_page"+ str(ex))

    def upload_file(self, path_to_file):
        self.wait_and_click('//input[@id="btnUpload"]')
        path_to_file = os.path.abspath(path_to_file)
        batch_name = f"Statement {datetime.datetime.utcnow().strftime('%m')} {datetime.datetime.utcnow().strftime('%Y')}"
        self.modal_dialog_process(path_to_file, batch_name)
        file_name = os.path.basename(path_to_file)
        #TODO MOCK
        com.log_message("MOCK - bot not go to page when file downloaded")
        if self.testMode:

            pass
        else:
            self.wait_element(f'//td[contains(., "{file_name}")]')
            self.browser.go_back()

        self.browser.is_element_visible('//input[@id="btnUpload"]')
        return batch_name

    def modal_dialog_process(self, path_to_file, batch_name):
        self.browser.driver.switch_to.frame(self.browser.find_element("//iframe[@id ='ifrUpload']"))
        self.wait_element('//input[@id="File"]')
        self.browser.choose_file('//input[@id="File"]', path_to_file)
        self.browser.unselect_checkbox('//input[@id="Hold"]')
        self.browser.input_text_when_element_is_visible('//input[@id="BatchName"]', batch_name)

        # TODO Mock
        com.log_message("MOCK - not click submit")
        if not self.testMode:
            self.browser.click_element_when_visible('//input[@id="submit1"]')

        self.browser.driver.switch_to.parent_frame()

        # TODO Mock
        com.log_message("MOCK - click close")
        if self.testMode:
            self.browser.click_element_when_visible('//a/span[. = "close"]')


    def check_file_status(self, batch_name):
        self.browser.driver.refresh()

        # TODO Mock
        com.log_message("MOCK - check first file file and not necessary")
        if self.testMode:
            self.wait_element(f'//*[@id="frmBatches"]/div/table/tbody/tr/td[contains(., "Rosey B")]/following-sibling::td[4]')
            status = self.browser.find_element(
                f'//*[@id="frmBatches"]/div/table/tbody/tr/td[contains(., "Rosey B")]/following-sibling::td[4]')
        else:
            self.wait_element(f'//*[@id="frmBatches"]/div/table/tbody/tr/td[contains(., "{batch_name}")]')
            status = self.browser.find_element(f'//*[@id="frmBatches"]/div/table/tbody/tr/td[contains(., "{batch_name}")]/following-sibling::td[5]')

        return status

    def is_element_available(self, locator, timeout=90) -> bool:
        try:
            com.wait_element(self.browser, locator, timeout=timeout)
            return True
        except Exception as ex:
            return False

    def additional_authentication_required(self):
        if self.is_element_available('//*[@id="content"]/div/div/h2[text() = "Additional Authentication Required"]', 30):
            question: str = self.browser.find_element('//*[@id="authDiv"]/p/strong').text

            if 'what was your first job?' in question.lower():
                self.browser.input_text_when_element_is_visible('//*[@id="verifyAnswer"]'
                                    , self.credentials['What was your first job?'])
            elif 'which of your cousins is closest in age to you?' in question.lower():
                self.browser.input_text_when_element_is_visible('//*[@id="verifyAnswer"]'
                                    , self.credentials['Which of your cousins is closest in age to you?'])

            self.browser.click_element_when_visible('//*[@id="VerifyButton"]')

    def click_continue_in_alerts(self):
        time.sleep(3)
        if self.browser.is_element_visible('//*[@id="continueButton"]'):
            self.browser.click_element_when_visible('//*[@id="continueButton"]')

    def pass_alerts(self):
        flag =False
        max_count = 7
        count= 0
        while flag == False:
            self.click_continue_in_alerts()
            time.sleep(5)
            flag = self.is_element_available('//a[text()="Patient Tools"]')
            count+=1
            if count == max_count:
                flag=True







