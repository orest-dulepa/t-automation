import shutil
import sys
from robot.api import logger
from RPA.Browser.Selenium import Selenium
import os
import datetime
import time
import io


def log_message(message, level='INFO', console=True):
    log_switcher = {
        'TRACE': logger.trace,
        'INFO': logger.info,
        'WARN': logger.warn,
        'ERROR': logger.error
    }
    if level.upper() == 'TRACE':
        trace_logger(message)
        return
    if not level.upper() in log_switcher.keys() or level.upper() == 'INFO':
        log_switcher.get(level.upper(), logger.info)(message, True, console)
        trace_logger(message)
    else:
        if level.upper() == 'ERROR':
            logger.info(message, True, console)
        else:
            log_switcher.get(level.upper(), logger.error)(message, True)
        trace_logger(message)


def print_version(extra: str = ''):
    try:
        file = open('VERSION')
        try:
            print('Version ' + file.read().strip() + extra)
        except:
            print('Error reading VERSION file')
        finally:
            file.close()
    except:
        log_message('VERSION file not found')


def get_screenshot_path(text):
    return (os.path.join(
        os.environ.get("ROBOT_ROOT", os.getcwd()),
        'output',
        text))


def close_specific_windows(browser: Selenium, selector: str):
    try:
        if browser.does_page_contain_element(selector):
            elements = browser.find_elements(selector)
            try:
                for element in elements:
                    if element.is_displayed():
                        log_message(
                            'A pop-up appeared and the bot closed it. Please validate the screenshot of the pop-up in the artifacts.',
                            'ERROR')
                        browser.capture_page_screenshot(
                            os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output',
                                         'Pop_up_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))
                        element.click()
                        browser.wait_until_element_is_not_visible(
                            '({})[{}]'.format(selector, elements.index(element) + 1))
            except:
                time.sleep(1)
    except:
        pass


def wait_element(browser: Selenium, locator: str, timeout: int = 90, is_need_screen: bool = True):
    is_success = False
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

    while not is_success and timer > datetime.datetime.now():
        close_specific_windows(browser, "//button[text()='Done']")
        close_specific_windows(browser, "//button[@id='_pendo-close-guide_']")
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


def contains_lower_xpath(text: str, item: str = 'text()') -> str:
    return f'contains(translate({item}, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"),"{text.lower()}")'


def take_screenshot(browser: Selenium, text: str):
    browser.capture_page_screenshot(
        os.path.join(os.environ.get(
            "ROBOT_ROOT", os.getcwd()),
            'output',
            f'{text} - {datetime.datetime.now().strftime("%H_%M_%S")}.png')
    )


def trace_logger(message: str):
    log_file = open(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'trace.log'), "a")
    log_file.write('{} - {}\n'.format(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), message))
    log_file.close()


def log_DOM(browser: Selenium):
    file_path = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output',
                             f'page_{datetime.datetime.utcnow().strftime("%Y-%m-%d_%H_%M_%S")}.html')
    trace_logger('=== HERE GOES DOM LOG ===> ' + str(file_path))
    try:
        with io.open(file_path, "w", encoding="utf-8") as f:
            f.write(browser.get_source())
    except Exception as ex:
        trace_logger('Failed to write DOM log: ' + str(ex))


def win32_cache_cleanup():
    python_version = str(sys.version_info.major) + '.' + str(sys.version_info.minor)
    cache_path = os.environ['USERPROFILE'] + r"\AppData\Local\Temp\gen_py\ ".strip() + python_version
    try:
        from subprocess import STDOUT, check_output
        check_output(["takeown", "/f", cache_path, "/r", "/d", "Y"], stderr=STDOUT)
    except:
        os.chmod(cache_path, 0o775)
    shutil.rmtree(cache_path)


def get_env() -> str:
    try:
        file = open('ENV')
        file.close()
        return 'PROD'
    except:
        return 'DEV'


def generate_creds(env, creds):
    a = {}
    for key, value in creds.items():
        if 'outlook' in key:
            a[key] = value
        else:
            a[key] = f'({env}) ' + value
    return a
