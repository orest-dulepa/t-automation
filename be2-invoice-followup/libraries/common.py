from robot.libraries.BuiltIn import BuiltIn
import datetime
import time
from robot.api import logger
import os


def log_message(message, level='INFO', console=True):
    log_switcher = {
        'TRACE': logger.trace,
        'INFO': logger.info,
        'WARN': logger.warn,
        'ERROR': logger.error
    }
    if not level.upper() in log_switcher.keys() or level.upper() == 'INFO':
        log_switcher.get(level.upper(), logger.info)(message, True, console)
    else:
        if level.upper() == 'ERROR':
            logger.info(message, True, console)
        else:
            log_switcher.get(level.upper(), logger.error)(message, True)


def close_specific_windows(browser, selector):
    try:
        if browser.does_page_contain_element(selector):
            elements = browser.find_elements(selector)
            try:
                for element in elements:
                    if element.is_displayed():
                        log_message('A pop-up appeared and the bot closed it. Please validate the screenshot of the pop-up in the artifacts.', 'ERROR')
                        browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'Pop_up_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))
                        element.click()
            except:
                time.sleep(1)
    except:
        pass


def wait_element(browser, selector, timeout=60, is_need_screen=True):
    is_success = False
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

    while not is_success and timer > datetime.datetime.now():
        close_specific_windows(browser, '//button[text()="Done"]')
        close_specific_windows(browser, '//button[contains(@id, "pendo-close-guide")]')
        close_specific_windows(browser, '//button[text()="Okay, got it!"]')
        close_specific_windows(browser, '//button[text()="Remind Me Later"]')
        close_specific_windows(browser, '//button[text()="REGISTER NOW"]')

        if browser.does_page_contain_element(selector):
            try:
                elem = browser.find_element(selector)
                is_success = elem.is_displayed()
            except:
                time.sleep(1)
    if not browser.does_page_contain_element(selector) and is_need_screen:
        log_message('Element \'{}\' not available'.format(selector), 'ERROR')
        browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'Element_not_available_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))


def wait_element_and_refresh(browser, selector, timeout=120, is_need_screen=True):
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

    while not browser.does_page_contain_element(selector) and timer > datetime.datetime.now():
        wait_element(browser, selector, 30, False)
        if browser.does_page_contain_element("//div[@class='loginError']"):
            browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'Login_Error_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))
            break
        if not browser.does_page_contain_element(selector):
            browser.reload_page()
    if not browser.does_page_contain_element(selector) and is_need_screen:
        log_message('Element \'{}\' not available'.format(selector), 'ERROR')
        browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'Element_not_available_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))


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
