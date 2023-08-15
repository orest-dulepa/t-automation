from RPA.Browser.Selenium import Selenium
from libraries import common
from urllib.parse import urlparse
import time
import os
import shutil


class Domo:

    def __init__(self, credentials: dict):
        self.browser: Selenium = Selenium()
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.login_to_domo()
        self.base_url: str = self.get_base_url()

    def get_base_url(self) -> str:
        parsed_uri = urlparse(self.url)
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

    def login_to_domo(self) -> None:
        self.browser.timeout = 60
        self.is_site_available = False
        count = 1
        path_to_temp = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'domo')
        if os.path.exists(path_to_temp):
            shutil.rmtree(path_to_temp)
        os.mkdir(path_to_temp)
        preferences = {
            'download.default_directory': os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'domo'),
            'plugins.always_open_pdf_externally': True,
            'download.directory_upgrade': True,
            'download.prompt_for_download': False
        }

        while count <= 3 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.url, preferences=preferences)
                self.browser.set_window_size(1920, 1080)
                if self.browser.does_page_contain_element("//a[text()='Use Direct Sign-On']"):
                    elem = self.browser.find_element("//a[text()='Use Direct Sign-On']")
                    if elem.is_displayed():
                        self.browser.click_element_when_visible("//a[text()='Use Direct Sign-On']")
                common.wait_element(self.browser, "//input[@name='username']")
                self.browser.input_text_when_element_is_visible("//input[@name='username']", self.login)
                self.browser.input_text_when_element_is_visible("//input[@name='password']", self.password)
                self.browser.wait_and_click_button("//button[@name='submit']")
                if self.browser.does_page_contain_element("//button[text()='Done']"):
                    self.browser.click_element_when_visible("//button[text()='Done']")
                common.wait_element_and_refresh(self.browser, "//h1[text()='Overview Page']", is_need_screen=False)
                self.is_site_available = self.browser.does_page_contain_element("//h1[text()='Overview Page']")
            except Exception as ex:
                common.log_message("Logging into DOMO. Attempt #'{} failed".format(count), 'ERROR')
                print(str(ex))
                self.browser.capture_page_screenshot(os.path.join(
                    os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'DOMO_login_failed_{}.png'.format(count)
                ))
                self.browser.close_browser()
            finally:
                count += 1

    def get_bcba_mapping(self) -> str:
        if self.browser.does_page_contain_element("//i[@class='icon-lines-horizontal md']"):
            self.browser.click_element_when_visible("//i[@class='icon-lines-horizontal md']")

        common.wait_element(self.browser, "//a/div/span[text()='Family Accounts']/../..")
        self.browser.double_click_element("//a/div/span[text()='Family Accounts']/../..")

        common.wait_element_and_refresh(self.browser, "//a[text()='Patient Clinician']")
        try:
            self.browser.click_element_when_visible("//a[text()='Patient Clinician']")
        except:
            time.sleep(1)
            self.browser.click_element_when_visible("//a[text()='Patient Clinician']")

        common.wait_element_and_refresh(self.browser, '//button[@aria-label="Share"]')
        self.browser.click_element_when_visible('//button[@aria-label="Share"]')

        common.wait_element(self.browser, '//div[text()="Send / Export"]')
        self.browser.click_element_when_visible('//div[text()="Send / Export"]')

        common.wait_element(self.browser, '//button[text()[contains(.,"Excel")]]')
        self.browser.click_element_when_visible('//button[text()[contains(.,"Excel")]]')

        path_to_file = common.get_downloaded_file_path(
            os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'domo'),
            '.xlsx',
            'Failed to download DOMO mapping.'
        )
        self.browser.close_window()
        return path_to_file
