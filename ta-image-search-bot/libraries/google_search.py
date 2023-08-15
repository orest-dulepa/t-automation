from RPA.Browser.Selenium import Selenium
from libraries import common
import datetime
import time


class GoogleSearch:

    def __init__(self, settings):
        self.browser = Selenium()
        self.url = settings['url']  # predefined
        self.search_term = settings['search_term']  # input
        self.search_section = settings['search_section']  # images
        self.is_site_available = False
        self.success = False
        self.initiate_browser()

    def initiate_browser(self):
        self.browser.close_browser()
        self.browser.timeout = 45

        count = 0
        self.is_site_available = False
        while count < 3 and self.is_site_available is False:
            count += 1
            try:
                self.browser.open_available_browser(self.url)
                self.browser.set_window_size(1920, 1080)
                self.browser.maximize_browser_window()
                self.close_specific_windows('//div[text()="I agree"]')
                self.browser.wait_until_page_contains_element("//input[@title='Search']")
                self.is_site_available = self.browser.does_page_contain_element("//input[@title='Search']")
            except Exception as ex:
                common.log_message(ex, 'TRACE')
                common.log_message("Google Web Page availability check. Attempt #{} failed".format(count), 'ERROR')
                self.browser.capture_page_screenshot(common.get_screenshot_path('image_search_failed_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))
                self.browser.close_browser()

    def perform_search(self):
        count = 0
        self.success = False
        while count < 3 and not self.success:
            count += 1
            try:
                self.close_specific_windows('//div[text()="I agree"]')
                self.browser.input_text_when_element_is_visible("//input[@title='Search']", self.search_term)
                self.browser.press_keys("//input[@title='Search']", "\ue007")
                self.success = True
            except Exception as ex:
                if count > 2:
                    raise ex
                self.success = False
                common.log_message(str(ex))
                self.browser.capture_page_screenshot(common.get_screenshot_path('image_search_failed_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))

    def take_first_element_screenshot(self):
        count = 0
        self.success = False
        while count < 3 and not self.success:
            count += 1
            try:
                self.close_specific_windows('//div[text()="I agree"]')
                self.browser.wait_until_page_contains_element("//div[@data-ri='0']")
                self.browser.capture_element_screenshot("//div[@data-ri='0']", common.get_screenshot_path(self.search_term + '.png'))
                self.success = True
            except Exception as ex:
                if count > 2:
                    raise ex
                self.success = False
                common.log_message(str(ex))
                self.browser.capture_page_screenshot(common.get_screenshot_path('image_search_failed_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))

    def close_specific_windows(self, selector: str) -> None:
        try:
            if self.browser.does_page_contain_element(selector):
                elements: list = self.browser.find_elements(selector)
                for element in elements:
                    try:
                        if element.is_displayed():
                            common.log_message('A pop-up appeared and the bot closed it. Please validate the screenshot of the pop-up in the artifacts.', 'ERROR')
                            self.browser.capture_page_screenshot(common.get_screenshot_path('Pop_up_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))
                            element.click()
                            self.browser.wait_until_element_is_not_visible('({})[{}]'.format(selector, elements.index(element) + 1))
                    except Exception as ex:
                        common.log_message(str(ex))
                        time.sleep(1)
        except Exception as e:
            common.log_message(str(e))
