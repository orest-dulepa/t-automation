import datetime
import time
from robot.api import logger
import os
from RPA.Browser.Selenium import Selenium
from libraries.google_sheets import GoogleSheets


google_logger: GoogleSheets = None


def dev_logger(message: str, level: str):
    try:
        log_file = open(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'dev.log'), "a")
        log_file.write('{} - {} - {}\n'.format(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), level, message))
        log_file.close()
    except Exception as ex:
        print(str(ex))


def initialize_google_logger(folder_name: str, file_name: str):
    global google_logger
    google_logger = GoogleSheets()
    google_logger.create_new_spreadsheet(folder_name, file_name)


def custom_logger(message: str):
    log_file = open(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'billing_scrub.log'), "a")
    log_file.write('{} - {}\n'.format(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), message))
    log_file.close()


def log_message(message: str, level: str = 'INFO', console: bool = True):
    log_switcher = {
        'TRACE': logger.trace,
        'INFO': logger.info,
        'WARN': logger.warn,
        'ERROR': logger.error
    }
    if google_logger and level.upper() in ['INFO', 'WARN', 'ERROR']:
        google_logger.update_spreadsheet(datetime.datetime.utcnow().strftime('%I:%M:%S %p'), level.upper(), message)
    if not level.upper() in log_switcher.keys() or level.upper() == 'INFO':
        logger.info(message, True, console)
    else:
        if level.upper() == 'ERROR':
            logger.info(message, True, console)
        else:
            log_switcher.get(level.upper(), logger.error)(message, True)
    dev_logger(message, level)


def close_specific_windows(browser: Selenium, selector: str):
    try:
        if browser.does_page_contain_element(selector):
            elements = browser.find_elements(selector)
            try:
                for element in elements:
                    if element.is_displayed():
                        log_message('A pop-up appeared and the bot closed it. Please validate the screenshot of the pop-up in the artifacts.', 'ERROR')
                        browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'Pop_up_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))
                        element.click()
                        browser.wait_until_element_is_not_visible('({})[{}]'.format(selector, elements.index(element) + 1))
            except:
                time.sleep(1)
    except:
        pass


def click_and_wait(browser: Selenium, locator_for_click: str, locator_for_wait: str, timeout: int = 90):
    is_success = False
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

    while not is_success and timer > datetime.datetime.now():
        try:
            wait_element(browser, locator_for_click, is_need_screen=False)
            browser.click_element_when_visible(locator_for_click)
            wait_element(browser, locator_for_wait, timeout=10, is_need_screen=False)

            browser.wait_until_element_is_not_visible(
                '//div[@data-bind="visible: loading()" and not(@style="display: none;")]'
            )

            if browser.does_page_contain_element(locator_for_wait):
                try:
                    elem = browser.find_element(locator_for_wait)
                    is_success = elem.is_displayed()
                except:
                    time.sleep(1)
        except:
            time.sleep(1)


def check_scheduled_maintenance(browser: Selenium):
    if browser.does_page_contain_element("//p[text()='Scheduled Maintenance']"):
        if browser.find_element("//p[text()='Scheduled Maintenance']").is_displayed():
            log_message("Data processing stopped due to Scheduled Maintenance. Please run the bot again when the CR is available", 'ERROR')
            browser.capture_page_screenshot(
                os.path.join(
                    os.environ.get("ROBOT_ROOT", os.getcwd()),
                    'output',
                    'Centralreach_scheduled_maintenance.png')
            )
            exit(1)


def wait_element(browser: Selenium, locator: str, timeout: int = 90, is_need_screen: bool = True):
    is_success = False
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

    while not is_success and timer > datetime.datetime.now():
        close_specific_windows(browser, '//button[text()="Done"]')
        close_specific_windows(browser, '//button[contains(@id, "pendo-close-guide")]')
        close_specific_windows(browser, '//button[text()="Okay, got it!"]')
        close_specific_windows(browser, '//button[text()="Remind Me Later"]')
        close_specific_windows(browser, '//button[text()="REGISTER NOW"]')

        check_scheduled_maintenance(browser)

        if browser.does_page_contain_element(locator):
            try:
                elem = browser.find_element(locator)
                is_success = elem.is_displayed()
            except:
                time.sleep(1)
        if not is_success:
            if browser.does_page_contain_element(
                    "//div[@id='select2-drop']/ul[@class='select2-results']/li[@class='select2-no-results']"
            ):
                elem = browser.find_element(
                    "//div[@id='select2-drop']/ul[@class='select2-results']/li[@class='select2-no-results']"
                )
                if elem.is_displayed():
                    break
    if not is_success and is_need_screen:
        log_message('Element \'{}\' not available'.format(locator), 'ERROR')
        browser.capture_page_screenshot(
            os.path.join(os.environ.get(
                "ROBOT_ROOT", os.getcwd()),
                'output',
                'Element_not_available_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
            )
        )


def wait_element_and_refresh(browser: Selenium, locator: str, timeout: int = 120, is_need_screen: bool = True):
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)
    is_success = False

    while not is_success and timer > datetime.datetime.now():
        wait_element(browser, locator, 30, False)
        if browser.does_page_contain_element(locator):
            try:
                elem = browser.find_element(locator)
                is_success = elem.is_displayed()
                if not is_success:
                    browser.reload_page()
            except Exception as ex:
                print(str(ex))
                browser.reload_page()
                time.sleep(1)
        else:
            browser.reload_page()
    if not browser.does_page_contain_element(locator) and is_need_screen:
        log_message('Element \'{}\' not available'.format(locator), 'ERROR')
        browser.capture_page_screenshot(
            os.path.join(
                os.environ.get("ROBOT_ROOT", os.getcwd()),
                'output',
                'Element_not_available_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
            )
        )


def get_downloaded_file_path(path_to_temp: str, extension: str, error_message: str) -> str:
    downloaded_files = []
    timer = datetime.datetime.now() + datetime.timedelta(0, 60 * 5)

    while timer > datetime.datetime.now():
        time.sleep(1)
        downloaded_files = [f for f in os.listdir(path_to_temp) if os.path.isfile(os.path.join(path_to_temp, f))]
        if len(downloaded_files) > 0 and downloaded_files[0].endswith(extension):
            time.sleep(1)
            break
    if len(downloaded_files) == 0:
        raise Exception(error_message)
    file_path = os.path.join(path_to_temp, downloaded_files[0])
    return file_path


def print_version():
    try:
        file = open('VERSION')
        try:
            print('Version {}'.format(file.read()))
        except Exception as ex:
            print('Error reading VERSION file. {}'.format(str(ex)))
        finally:
            file.close()
    except Exception as e:
        log_message('VERSION file not found. {}'.format(str(e)))
