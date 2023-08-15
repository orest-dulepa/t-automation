import datetime
import time
from robot.api import logger
import os
from RPA.Browser.Selenium import Selenium
import shutil


def custom_logger(message: str):
    log_file = open(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'billing_scrub.log'), "a")
    log_file.write('{} - {}\n'.format(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), message))
    log_file.close()


def get_path_to_output():
    return os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output')


def take_screenshot(browser, name: str = "error_screenshot", is_error = True):
    name = name.replace(" ", "_")

    if is_error:
        screenshot_reason = f'error_screenshot_{name}'
    else:
        screenshot_reason = name

    browser.capture_page_screenshot(
        os.path.join(os.environ.get(
            "ROBOT_ROOT", os.getcwd()),
            'output',
            f"{screenshot_reason}_{datetime.datetime.now().strftime('%H_%M_%S')}.png"
        )
    )

def take_screenshot_of_client_to_save_in_temp(browser, name):
    name = name.replace(" ", "_")
    path_to_screen = os.path.join(os.environ.get(
            "ROBOT_ROOT", os.getcwd()),
            'temp',
            f"{name}_{datetime.datetime.now().strftime('%H_%M_%S')}.png")
    browser.capture_page_screenshot(path_to_screen)
    return path_to_screen


def log_message(message: str, level: str = 'INFO', console: bool = True):
    log_switcher = {
        'TRACE': logger.trace,
        'INFO': logger.info,
        'WARN': logger.warn,
        'ERROR': logger.error
    }
    if not level.upper() in log_switcher.keys() or level.upper() == 'INFO':
        logger.info(message, True, console)
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


def click_and_wait(browser: Selenium, locator_for_click: str, locator_for_wait: str, timeout: int = 90):
    is_success = False
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

    while not is_success and timer > datetime.datetime.now():
        close_specific_windows(browser, "//button[text()='Done']")
        close_specific_windows(browser, "//button[@id='_pendo-close-guide_']")
        try:
            wait_element(browser, locator_for_click)
            browser.click_element_when_visible(locator_for_click)
            wait_element(browser, locator_for_wait, timeout=10)

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

    if not is_success:
        raise Exception(f"Click and wait error {locator_for_click} ")


def wait_element(browser: Selenium, locator: str, timeout: int = 60):
    is_success = False
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

    while not is_success and timer > datetime.datetime.now():
        close_specific_windows(browser, "//button[text()='Done']")
        close_specific_windows(browser, "//button[@id='_pendo-close-guide_']")
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

    if not is_success:
        raise Exception(f"Wait error - Element not available'{locator}'")

def check_scheduled_maintenance(browser):
    if browser.does_page_contain_element("//p[text()='Scheduled Maintenance']"):
        if browser.find_element("//p[text()='Scheduled Maintenance']").is_displayed():
            browser.capture_page_screenshot(
                os.path.join(
                    os.environ.get("ROBOT_ROOT", os.getcwd()),
                    'output',
                    'Centralreach_scheduled_maintenance.png')
            )
            raise Exception("Data processing stopped due to Scheduled Maintenance. Please run the bot again when the CR is available")



def wait_element_and_refresh(browser: Selenium, locator: str, timeout: int = 120, is_need_screen: bool = True):
    timer = datetime.datetime.now() + datetime.timedelta(0, timeout)
    is_success = False

    while not is_success and timer > datetime.datetime.now():
        wait_element(browser, locator, 30)
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


def get_downloaded_file_path(path_to_temp: str, extension: str, error_message: str="Unable to get downloaded file path") -> str:
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


def move_file_to_output(path_to_file: str, new_file_name: str):
    is_success = False
    count = 0
    attempts = 5
    exception: Exception = Exception()
    while (count < attempts) and (is_success is False):
        try:
            src_path = os.path.abspath(path_to_file)
            new_file_name = new_file_name.replace("/", '_')
            dst_path = os.path.abspath(os.path.join(get_path_to_output(), new_file_name))
            shutil.move(src_path, dst_path)
            return dst_path
        except Exception as ex:
            time.sleep(2)
            exception = Exception(f"Unable moving file - {path_to_file} to output folder. " + str(ex))
            count += 1

    if is_success is False:
        raise exception


def move_file_to_temp(path_to_file: str, new_file_name: str):
    is_success = False
    count = 0
    attempts = 5
    exception: Exception = Exception()
    while (count < attempts) and (is_success is False):
        try:
            src_path = os.path.abspath(path_to_file)
            new_file_name = new_file_name.replace("/", '_')
            dst_path = os.path.abspath(os.path.join("temp", new_file_name))
            shutil.move(src_path, dst_path)
            return dst_path
        except Exception as ex:
            time.sleep(2)
            exception = Exception(f"Unable moving file - {path_to_file} to temp folder. " + str(ex))
            count += 1

    if is_success is False:
        raise exception



contacts_mandatory_columns = [
      "rn",
      "Id",
      "ImgProfile",
      "Credentials",
      "FirstName",
      "LastName",
      "PermissionId",
      "Email",
      "LastLoginDate",
      "GuardianFirstName",
      "GuardianLastName",
      "TypeId",
      "IsActive",
      "LastDeactivatedOn",
      "LastDeactivatedBy",
      "LastReactivatedOn",
      "LastReactivatedBy",
      "CreationDate",
      "Type",
      "Labels",
      "AddressLine1",
      "AddressLine2",
      "City",
      "StateProvince",
      "ZipPostalCode",
      "Country",
      "PhoneHome",
      "PhoneCell",
      "PhoneWork",
      "HomeAddressLine1",
      "HomeAddressLine2",
      "HomeCity",
      "HomeStateProvince",
      "HomeZipPostalCode",
      "HomeCountry",
      "HomePhoneHome",
      "HomePhoneCell",
      "HomePhoneWork",
      "PrimaryLocationId",
      "PrimaryLocationName",
      "BirthDate",
      "Gender",
      "Principals"
]

billings_mandatory_columns = [
    "Id",
    "DateOfService",
    "ClientId",
    "ClientFirstName",
    "ClientLastName",
    "ProcedureCode",
    "ProcedureCodeDescription",
    "UnitsOfService",
    "AmountAgreedOwed",
    "CopayOwed",
    "LastInvoiceId",
    "LastInvoiceDate",
    "LastCopayInvoiceId",
    "LastCopayInvoiceDate",
    "MailToFirstName",
    "MailToLastName",
    "MailToAddress1",
    "MailToAddress2+A:V",
    "MailToCity",
    "MailToState",
    "MailToZip",
    "CostShareDue",
    "StatementID",
    "StatementDate"
]

billings_mandatory_columns_for_csc = [
    "Id",
    "DateOfService",
    "ClientId",
    "ClientFirstName",
    "ClientLastName",
    "ProcedureCode",
    "ProcedureCodeDescription",
    "UnitsOfService",
    "AmountAgreedOwed",
    "CopayOwed",
    "LastInvoiceId",
    "LastInvoiceDate",
    "LastCopayInvoiceId",
    "LastCopayInvoiceDate"
]

billings_mandatory_columns_formulas = [
    "MailToFirstName",
    "MailToLastName",
    "MailToAddress1",
    "MailToAddress2+A:V",
    "MailToCity",
    "MailToState",
    "MailToZip",
    "CostShareDue",
    "StatementID",
    "StatementDate"
]

billings_excess_columns_= [
    "AmountAgreedOwed",
    "CopayOwed",
    "LastInvoiceId",
    "LastInvoiceDate",
    "LastCopayInvoiceId",
    "LastCopayInvoiceDate",
]