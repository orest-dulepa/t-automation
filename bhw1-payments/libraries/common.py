import datetime
import time
import os

from robot.api import logger
from RPA.Browser.Selenium import Selenium
from RPA.Robocloud.Items import Items


def create_output_dir():
    try:
        os.mkdir("output")
    except FileExistsError:
        pass


def get_path_to_output():
    return os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "output")


def log_message(message, level="INFO", console=True):
    log_switcher = {
        "TRACE": logger.trace,
        "INFO": logger.info,
        "WARN": logger.warn,
        "ERROR": logger.error,
    }
    if not level.upper() in log_switcher.keys() or level.upper() == "INFO":
        log_switcher.get(level.upper(), logger.info)(message, True, console)
    else:
        if level.upper() == "ERROR":
            logger.info(message, True, console)
        else:
            log_switcher.get(level.upper(), logger.error)(message, True)


def close_specific_windows(browser: Selenium, selector: str):
    try:
        if browser.does_page_contain_element(selector):
            elements = browser.find_elements(selector)
            try:
                for element in elements:
                    if element.is_displayed():
                        log_message(
                            "A pop-up appeared and the bot closed it. Please validate the screenshot of the pop-up in the artifacts.",
                            "ERROR",
                        )
                        browser.capture_page_screenshot(
                            os.path.join(
                                os.environ.get("ROBOT_ROOT", os.getcwd()),
                                "output",
                                "Pop_up_{}.png".format(
                                    datetime.datetime.now().strftime("%H_%M_%S")
                                ),
                            )
                        )
                        element.click()
                        browser.wait_until_element_is_not_visible(
                            "({})[{}]".format(selector, elements.index(element) + 1)
                        )
            except:
                time.sleep(1)
    except:
        pass


def wait_element(
    browser: Selenium, locator: str, timeout: int = 60, is_need_screen: bool = True
):
    is_success = False
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

    while not is_success and timer > datetime.datetime.now():
        close_specific_windows(browser, '//button[text()="Done"]')
        close_specific_windows(browser, '//button[contains(@id, "pendo-close-guide")]')
        close_specific_windows(browser, '//button[text()="Okay, got it!"]')
        close_specific_windows(browser, '//button[text()="Remind Me Later"]')
        close_specific_windows(browser, '//button[text()="REGISTER NOW"]')

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
        log_message("Element '{}' not available".format(locator), "ERROR")
        browser.capture_page_screenshot(
            os.path.join(
                os.environ.get("ROBOT_ROOT", os.getcwd()),
                "output",
                "Element_not_available_{}.png".format(
                    datetime.datetime.now().strftime("%H_%M_%S")
                ),
            )
        )


def print_version():
    try:
        file = open("VERSION")
        try:
            print("Version " + file.read())
        except Exception as ex:
            print("Error reading VERSION file")
        finally:
            file.close()
    except Exception as e:
        log_message("VERSION file not found")


def get_screenshot_path(text):
    return os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "output", text)


def wait_element_and_refresh(browser, selector, timeout=120, is_need_screen=True):
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

    while (
        not browser.does_page_contain_element(selector)
        and timer > datetime.datetime.now()
    ):
        wait_element(browser, selector, 30, False)
        if browser.does_page_contain_element("//div[@class='loginError']"):
            browser.capture_page_screenshot(
                os.path.join(
                    os.environ.get("ROBOT_ROOT", os.getcwd()),
                    "output",
                    "Login_Error_{}.png".format(
                        datetime.datetime.now().strftime("%H_%M_%S")
                    ),
                )
            )
            break
        if not browser.does_page_contain_element(selector):
            browser.reload_page()
    if not browser.does_page_contain_element(selector) and is_need_screen:
        log_message("Element '{}' not available".format(selector), "ERROR")
        browser.capture_page_screenshot(
            os.path.join(
                os.environ.get("ROBOT_ROOT", os.getcwd()),
                "output",
                "Element_not_available_{}.png".format(
                    datetime.datetime.now().strftime("%H_%M_%S")
                ),
            )
        )


def get_downloaded_file_path(
    path_to_temp,
    extension,
    error_message="Unable to get downloaded file path",
):
    downloaded_files = []
    timer = datetime.datetime.now() + datetime.timedelta(0, 10)

    while timer > datetime.datetime.now():
        time.sleep(1)
        downloaded_files = [
            f
            for f in os.listdir(path_to_temp)
            if os.path.isfile(os.path.join(path_to_temp, f))
        ]
        if len(downloaded_files) > 0 and downloaded_files[0].endswith(extension):
            time.sleep(1)
            break
    if len(downloaded_files) == 0:
        raise Exception(error_message)
    file_path = os.path.join(path_to_temp, downloaded_files[0])
    return file_path


def move_file_to_output(path_to_file: str, new_file_name: str):
    is_success = False
    count = 0
    attempts = 5
    exception: Exception = Exception()
    while (count < attempts) and (is_success is False):
        try:
            src_path = os.path.abspath(path_to_file)
            new_file_name = new_file_name.replace("/", "_")
            dst_path = os.path.abspath(
                os.path.join(get_path_to_output(), new_file_name)
            )
            os.rename(src_path, dst_path)
            return dst_path
        except Exception as ex:
            time.sleep(2)
            exception = Exception(
                f"Unable moving file - {path_to_file} to output folder. " + str(ex)
            )
            count += 1

    if is_success is False:
        raise exception
