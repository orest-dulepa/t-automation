from robot.api import logger
from RPA.Browser.Selenium import Selenium
import datetime
import time
import os
import pandas as pd
import re
from collections.abc import Iterable


def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes, dict)):
            yield from flatten(el)
        else:
            yield el


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


def wait_element(
    browser: Selenium, locator: str, timeout: int = 60, is_need_screen: bool = True
):
    is_success = False
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

    while not is_success and timer > datetime.datetime.now():
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
