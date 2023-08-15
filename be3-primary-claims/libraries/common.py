import datetime
import time
from robot.api import logger
import os
import re
from RPA.Browser.Selenium import Selenium
from RPA.PDF import PDF


def log_message(message: str, level: str = 'INFO', console: bool = True):
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


def wait_element(browser: Selenium, selector: str, timeout: int = 60, is_need_screen: bool = True):
    is_success = False
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

    while not is_success and timer > datetime.datetime.now():
        close_specific_windows(browser, "//button[text()='Done']")
        close_specific_windows(browser, "//button[@id='_pendo-close-guide_']")
        if browser.does_page_contain_element(selector):
            try:
                elements = browser.find_elements(selector)
                for elem in elements:
                    if elem.is_displayed():
                        is_success = True
                        break
            except:
                time.sleep(1)
    if not browser.does_page_contain_element(selector) and is_need_screen:
        log_message('Element \'{}\' not available'.format(selector), 'ERROR')
        browser.capture_page_screenshot(
            os.path.join(
                os.environ.get("ROBOT_ROOT", os.getcwd()),
                'output',
                'Element_not_available_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
            )
        )


def wait_element_and_refresh(browser: Selenium, selector: str, timeout: int = 120, is_need_screen: bool = True):
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

    while not browser.does_page_contain_element(selector) and timer > datetime.datetime.now():
        wait_element(browser, selector, 45, False)
        if browser.does_page_contain_element("//div[@class='loginError']"):
            browser.capture_page_screenshot(
                os.path.join(
                    os.environ.get("ROBOT_ROOT", os.getcwd()),
                    'output',
                    'Login_Error_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
                )
            )
            break
        if not browser.does_page_contain_element(selector):
            browser.reload_page()
            browser.reload_page()
            browser.reload_page()
    if not browser.does_page_contain_element(selector) and is_need_screen:
        log_message('Element \'{}\' not available'.format(selector), 'ERROR')
        browser.capture_page_screenshot(
            os.path.join(
                os.environ.get("ROBOT_ROOT", os.getcwd()),
                'output',
                'Element_not_available_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))
            )
        )


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


timezones = {
    "MST": -7,
    "EST": -5,
    "PST": -8,
    "CST": -6,
    "AKST": -9,
}


def convert_date(date: str) -> (int, int, int):
    date = date.split('/')
    year = datetime.datetime.utcnow().year
    if len(date[2]) == 4:
        year = int(date[2])
    if len(date[2]) == 2:
        year = int('20' + date[2])
    month = int(date[0])
    day = int(date[1])
    return year, month, day


def pre_parse_time_cr(time_str: str) -> (str, str, str, str, str):
    time_str = time_str.split(' ')
    time_z = time_str[-1]
    time_str = time_str[0].split('-')
    start_time_str = time_str[0]
    end_time_str = time_str[1]
    am_or_pm_end = end_time_str[-1]
    if start_time_str[-1] in ['a', 'p']:
        am_or_pm_start = start_time_str[-1]
        start_time_str = start_time_str[0:-1]
    else:
        am_or_pm_start = am_or_pm_end
    end_time_str = end_time_str[0: len(end_time_str) - 1]
    return start_time_str, end_time_str, time_z, am_or_pm_start, am_or_pm_end


def parse_time_cr(time_str: str) -> (int, int):
    if ':' in time_str:
        time_str = time_str.split(':')
        hours = int(time_str[0])
        minutes = int(time_str[1])
    else:
        hours = int(time_str)
        minutes = 0
    return hours, minutes


def parse_time_pdf(time_str):
    time_str = time_str.split(' ')
    am_pm = 'a'
    if time_str[-1] in ['AM', 'PM']:
        am_pm = 'a' if time_str[-1] == 'AM' else 'p'
    time_str = time_str[0].split(':')
    hours = int(time_str[0])
    minutes = int(time_str[1])
    return hours, minutes, am_pm


def convert_time_new(hours, minutes, year, month, day, am_or_pm, time_z) -> datetime:
    res_time = datetime.datetime(year=year, month=month, day=day, hour=hours, minute=minutes)
    if am_or_pm == 'p' and hours != 12:
        res_time += datetime.timedelta(hours=12)
    res_time += datetime.timedelta(hours=timezones.get(time_z))
    return res_time


def pdf_times_process(times_pdf: list):
    start_time_list = parse_time_pdf(times_pdf[0])
    end_time_list = parse_time_pdf(times_pdf[1])
    if start_time_list[2] == end_time_list[2]:
        start_time = datetime.time(start_time_list[0], start_time_list[1])
        end_time = datetime.time(end_time_list[0], end_time_list[1])
        if start_time_list[0] == 12:
            start_time = datetime.time(0, start_time_list[1])
        if end_time_list[0] == 12:
            end_time = datetime.time(0, end_time_list[1])
        if end_time < start_time:
            end_time_list, start_time_list = start_time_list, end_time_list
    elif start_time_list[2] == 'p' and end_time_list[2] == 'a':
        end_time_list, start_time_list = start_time_list, end_time_list
    return [start_time_list, end_time_list]


def compare_times_cr_pdf(time_str_cr: str, times_pdf: list) -> bool:
    start_time_str, end_time_str, time_z, am_or_pm_start, am_or_pm_end = pre_parse_time_cr(time_str_cr)
    hours_start, minutes_start = parse_time_cr(start_time_str)
    hours_end, minutes_end = parse_time_cr(end_time_str)
    start_time_pdf_hours, start_time_pdf_minutes, start_time_pdf_am_pm = times_pdf[0]
    end_time_pdf_hours, end_time_pdf_minutes, end_time_pdf_am_pm = times_pdf[1]
    if hours_start != start_time_pdf_hours:
        return False
    if hours_end != end_time_pdf_hours:
        return False
    if minutes_start != start_time_pdf_minutes:
        return False
    if minutes_end != end_time_pdf_minutes:
        return False
    if am_or_pm_start != start_time_pdf_am_pm:
        return False
    if am_or_pm_end != end_time_pdf_am_pm:
        return False
    return True


def pdf_location_timing_check(pdf: PDF, pdf_file: str) -> tuple or str:
    location = ''
    date = ''
    has_location = False
    has_time = False

    pdf.parse_pdf(pdf_file)
    first_page = pdf.rpa_pdf_document.get_page(1)
    times = []
    for line in range(len(first_page.content)):
        try:
            context = first_page.content[line].text
            if 'Location' in context:
                locs = re.findall(r'(\d{2}: .*?)(\s{2}|$)', context)
                location = locs[0][0]
                # print(locs)
                has_location = True
            if 'Time' in context:
                times += re.findall(r'\d{2}:\d{2} [A,P]M', context)
                if len(times) == 2:
                    # print(times)
                    has_time = True
            if 'Date' in context:
                date = re.findall(r'\d{2}/\d{2}/\d{4}', context)
        except:
            continue
        if has_location and has_time:
            break
    pdf.close_all_pdf_documents()
    if not has_location and not has_time:
        return 'Location and time are unknown'
    if not has_location:
        return 'Location is unknown'
    if not has_time:
        return 'Time is unknown'
    return location, times, date


def get_downloaded_file_path(path_to_temp: str, extension: str, error_message: str) -> str:
    downloaded_files = []
    timer = datetime.datetime.now() + datetime.timedelta(0, 60 * 3)

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
