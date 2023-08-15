from RPA.Browser.Selenium import Selenium
from libraries import common
from RPA.PDF import PDF
from urllib.parse import urlparse
import datetime
import time
import os
import shutil
import traceback
import sys
from ntpath import basename
from libraries import common as com
from config import BOT_MODE
from .exceptions import NoCRResults, NoBulkApply
from retry import retry


class CentralReach:
    def __init__(self, credentials: dict):
        self.selected_rows_count = 0
        self.browser: Selenium = Selenium()
        self.browser.timeout = 5
        self.url: str = credentials["url"]
        self.login: str = credentials["login"]
        self.password: str = credentials["password"]
        self.path_to_temp: str = os.path.join(
            os.environ.get("ROBOT_ROOT", os.getcwd()), "input"
        )
        self.base_url: str = self.get_base_url()
        self.login_to_central_reach()

    def get_base_url(self) -> str:
        parsed_uri = urlparse(self.url)
        base_url: str = "{uri.scheme}://{uri.netloc}/".format(uri=parsed_uri)
        return base_url

    def wait_filter_page_loads(self):
        com.wait_element(
            self.browser,
            "//table[@data-bind=\"css: {'use-agreed': listVm.useAgreedView() }\"]",
        )

    def wait_bulk_page_loads(self):
        com.wait_element(self.browser, "//button[@data-click='executeAllBulkPayments']")

    def filter_hide_headers(self):
        self.wait_filter_page_loads()
        self.browser.execute_javascript(
            "document.getElementsByTagName( 'thead' )[0].style.display = 'none'"
        )
        time.sleep(1)

    def filter_show_headers(self):
        self.wait_filter_page_loads()
        self.browser.execute_javascript(
            "document.getElementsByTagName( 'thead' )[0].style.display = 'block'"
        )

    def bulk_hide_headers(self):
        self.wait_bulk_page_loads()
        self.browser.execute_javascript(
            "document.getElementById( 'header' ).style.display = 'none';"
        )
        self.browser.execute_javascript(
            "document.getElementsByTagName( 'header' )[3].style.display = 'none'"
        )

    def filter_billing_data(self, start_date, end_date, client_id, invoice_type):
        if invoice_type == "ESCC":
            label_id = "3910"
        if invoice_type == "BHPN":
            label_id = "3911"

        self.browser.go_to(
            f"{self.base_url}#billingmanager/billing/?startdate={start_date}&enddate={end_date}&codeLabelIdIncluded={label_id}&billStatus=4&clientId={client_id}"
        )
        self.browser.reload_page()
        self.wait_filter_page_loads()

    def select_invoice_rows(self, apply_payments):
        self.wait_filter_page_loads()
        self.selected_rows_count = 0
        failed_apply_payments = []
        for payment in apply_payments:
            checkbox_xpath = "//a[@data-title='Click to view/edit this authorization' and contains(.,'{}')]/../..//span[contains(.,'{}')]/../..//input[@data-bind='checked: selected']".format(
                payment[1], payment[0].strftime("%-m/%d/%y")
            )
            try:
                if self.browser.is_checkbox_selected("({})[1]".format(checkbox_xpath)):
                    for i in range(2, 10):
                        if not self.browser.is_checkbox_selected(
                            "({})[{}]".format(checkbox_xpath, i)
                        ):
                            self.browser.select_checkbox(
                                "({})[{}]".format(checkbox_xpath, i)
                            )
                            break
                else:
                    self.browser.select_checkbox("({})[1]".format(checkbox_xpath))

                self.selected_rows_count += 1

            except:
                com.log_message("No such row in CR data for {}".format(payment))
                failed_apply_payments.append(payment)

        return failed_apply_payments

    def get_rows_cr_not_invoice(self):
        self.wait_filter_page_loads()
        rows_cr_not_invoice = []

        checkbox_xpath = "//input[@data-bind='checked: selected']"
        rows = self.browser.get_element_count(checkbox_xpath)

        for i in range(1, rows + 1):
            current_checkbox = "({})[{}]".format(checkbox_xpath, i)
            if not self.browser.is_checkbox_selected(current_checkbox):
                service_date = self.browser.get_text(
                    "{}/../..//span[@class='inline-block padding-xs-left']".format(
                        current_checkbox
                    )
                )
                cpt = self.browser.get_text(
                    "{}/../..//a[@data-title='Click to view/edit this authorization']".format(
                        current_checkbox
                    )
                )
                rows_cr_not_invoice.append((service_date, cpt))
                com.log_message(
                    "No such row in Invoice data for {} and {}".format(
                        service_date, cpt
                    )
                )

        return rows_cr_not_invoice

    def click_bulk_apply(self):
        self.wait_filter_page_loads()
        try:
            self.browser.click_element_when_visible("//a[@id='btnBillingPayment']")
        except AssertionError:
            raise NoBulkApply()

    def filter_check_rows_number(self, rows_number):
        self.wait_filter_page_loads()
        # If no results found - exit
        try:
            self.browser.wait_until_page_contains_element(
                "//input[@data-bind='checked: selected']", timeout=2
            )
        except AssertionError:
            raise NoCRResults()

        rows = self.browser.get_element_count("//input[@data-bind='checked: selected']")
        com.log_message("CR ROWS NUMBER: {}".format(rows))
        if rows != rows_number:
            com.log_message("Rows Number Invoice vs CR mismatch!")

    def bulk_check_rows_number(self):
        xpath = "//input[contains(@data-bind,'bulkPaymentAmount')]"
        count = self.browser.get_element_count(xpath)
        com.log_message(
            "Filter Page Selected Rows: {}".format(self.selected_rows_count)
        )
        com.log_message("Bulk Page Rows: {}".format(count))
        return count == self.selected_rows_count

    def bulk_check_total(self, total_payments):
        self.wait_bulk_page_loads()
        total = self.browser.get_text("//strong[@data-bind='text: amountsTotal']")
        com.log_message("CR TOTAL PAYMENTS: {}".format(total))
        if float(total) != float(total_payments):
            com.log_message("Total Amount of Pay Invoice vs CR mismatch!")

    def bulk_apply_payments(self, apply_payments):
        self.wait_bulk_page_loads()
        failed_apply_payments = []
        updated_inputs = []
        for payment in apply_payments:
            match = False
            input_xpath = "//td[@data-bind='shortDate: item.dateOfService' and .='{}']/..//span[@data-bind='text: item.procedureCodeString' and contains(.,'{}')]/../..//input[contains(@data-bind,'bulkPaymentAmount')]".format(
                payment[0].strftime("%m/%d"), payment[1]
            )
            input_count = self.browser.get_element_count(input_xpath)
            amount_to_pay = -1
            for i in range(1, input_count + 1):
                xpath = "({})[{}]".format(input_xpath, i)
                if xpath in updated_inputs:
                    continue
                amount_to_pay = self.browser.get_value(xpath)
                if float(amount_to_pay) == float(payment[2]):
                    match = True
                    break

            if not match and amount_to_pay != -1:
                com.log_message(
                    "Incorrect amount to pay: {} for {}".format(amount_to_pay, payment)
                )
                for i in range(1, input_count + 1):
                    xpath = "({})[{}]".format(input_xpath, i)
                    if xpath not in updated_inputs:
                        self.browser.input_text_when_element_is_visible(
                            xpath, str(payment[2])
                        )
                        updated_inputs.append(xpath)
                        break

                failed_apply_payments.append((payment, amount_to_pay))

        return failed_apply_payments

    def bulk_finish_payment(self, check_date, check_number, invoice_type):
        result = []

        self.browser.input_text_when_element_is_visible(
            "//input[@data-bind='datepicker: date']", check_date
        )
        self.browser.click_element_when_visible(
            "//strong[@data-bind='text: amountsTotal']"
        )
        self.browser.input_text_when_element_is_visible(
            "//input[contains(@data-bind,'value: reference')]", check_number
        )
        self.browser.select_from_list_by_value(
            "//select[contains(@data-bind,'options: paymentTypes')]", "4"
        )

        try:
            select_xpath = "//select[contains(@data-bind,'options: client.payorsUi')]"
            expected_label = ""
            if invoice_type == "ESCC":
                expected_label = "Primary: Easter Seals Southern California > Standard"
                self.browser.select_from_list_by_label(select_xpath, expected_label)
            if invoice_type == "BHPN":
                expected_label = "Primary: the BHPN > Standard"
                self.browser.select_from_list_by_label(select_xpath, expected_label)
        except:
            com.log_message("Payor selection error!")
            result.append(
                (expected_label, self.browser.get_selected_list_labels(select_xpath))
            )
            return result

        if BOT_MODE == "cancel":
            self.browser.click_element_when_visible("//button[@data-click='cancel']")
            com.log_message("CANCEL PAYMENT!")
        else:
            self.browser.click_element_when_visible(
                "//button[@data-click='executeAllBulkPayments']"
            )
            self.browser.wait_until_page_contains("Payments complete")
            com.log_message("PAYMENT COMPLETE!")

        return result

    def is_element_available(self, locator, timeout=90) -> bool:
        try:
            com.wait_element(self.browser, locator, timeout=timeout)
            return True
        except Exception as ex:
            return False

    @retry(Exception, delay=1, tries=3)
    def export_csv_contacts_file(self):
        self.browser.go_to(f"{self.base_url}#contacts/?filter=clients")
        file_name = "clients"
        try:
            self.browser.click_element_when_visible(
                '//button[i[contains(@class,"fa-cloud-download")]]'
            )
            self.browser.click_element_when_visible(
                '//button[i[contains(@class,"fa-cloud-download")]]/following-sibling::ul/li[a[text()="CSV"]]'
            )
            com.wait_element(
                self.browser, '//a[@type="button"and text()="Go To Files"]'
            )

            if self.is_element_available(
                '//div[contains(text(), "Your export has been started")]', timeout=5
            ):
                count = 0
                attempts = 3
                is_success = False
                timeout = 5
                exception: Exception = Exception()
                while (count < attempts) and (is_success is False):
                    try:
                        self.browser.reload_page()

                        self.browser.click_element_when_visible(
                            '//button[i[contains(@class,"fa-cloud-download")]]'
                        )
                        self.browser.click_element_when_visible(
                            '//button[i[contains(@class,"fa-cloud-download")]]/following-sibling::ul/li[a[text()="CSV"]]'
                        )
                        com.wait_element(
                            self.browser, '//*[@type="button"and text()="Go To Files"]'
                        )

                        com.wait_element(
                            self.browser,
                            '//h4/a[i[@class="fa fa-download"] and text()="Download"]',
                            timeout=timeout,
                        )
                        is_success = True
                    except Exception as ex:
                        exception = Exception("Download icon does not exist")
                        count += 1

                if not is_success:
                    raise exception

            com.wait_element(
                self.browser,
                '//h4/a[i[@class="fa fa-download"] and text()="Download"]',
                timeout=20,
            )
            self.browser.click_element_when_visible(
                '//h4/a[i[@class="fa fa-download"] and text()="Download"]'
            )
            downloaded_path_to_file = com.get_downloaded_file_path(
                path_to_temp=os.path.abspath("input"),
                extension=".csv",
                error_message="file not exist",
            )
            path_to_file = com.move_file_to_output(
                path_to_file=downloaded_path_to_file, new_file_name=file_name + ".csv"
            )
            self.browser.click_element_when_visible(
                '//button[@type="button"and text()="Close"]'
            )

            com.log_message(f"'{file_name}' file exported and downloaded")
            return path_to_file

        except Exception as ex:
            raise Exception(f"Unable to export '{file_name}'. " + str(ex), "WARN")

    def login_to_central_reach(self) -> None:
        self.browser.close_browser()
        self.is_site_available = False
        count = 1

        if os.path.exists(self.path_to_temp):
            shutil.rmtree(self.path_to_temp)
        os.mkdir(self.path_to_temp)
        self.browser.set_download_directory(self.path_to_temp, True)

        while count <= 3 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.url)
                self.browser.set_window_size(1920, 1080)
                self.browser.maximize_browser_window()
                common.wait_element(
                    self.browser,
                    "//input[@type='password']",
                    is_need_screen=False,
                    timeout=10,
                )
                if self.browser.does_page_contain_element(
                    "//p[text()='Scheduled Maintenance']"
                ):
                    if self.browser.find_element(
                        "//p[text()='Scheduled Maintenance']"
                    ).is_displayed():
                        common.log_message(
                            "Logging into CentralReach failed. Scheduled Maintenance.".format(
                                count
                            ),
                            "ERROR",
                        )
                        self.browser.capture_page_screenshot(
                            os.path.join(
                                os.environ.get("ROBOT_ROOT", os.getcwd()),
                                "output",
                                "Centralreach_scheduled_maintenance.png",
                            )
                        )
                        return
                common.wait_element(
                    self.browser, "//input[@type='password']", is_need_screen=False
                )
                self.browser.input_text_when_element_is_visible(
                    "//input[@type='text']", self.login
                )
                self.browser.input_text_when_element_is_visible(
                    "//input[@type='password']", self.password
                )
                self.browser.click_button_when_visible("//button[@class='btn']")
                if self.browser.does_page_contain_element(
                    '//div[@class="loginError"]/div[text()="There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support"]'
                ):
                    elem = self.browser.find_element(
                        '//div[@class="loginError"]/div[text()="There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support"]'
                    )
                    if elem.is_displayed():
                        common.log_message(
                            "Logging into CentralReach failed. There was an unexpected problem signing in.".format(
                                count
                            ),
                            "ERROR",
                        )
                        raise Exception(
                            "There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support"
                        )
                common.wait_element_and_refresh(
                    self.browser, "//span[text()='Favorites']", is_need_screen=False
                )
                self.is_site_available = self.browser.does_page_contain_element(
                    "//span[text()='Favorites']"
                )
            except Exception as ex:
                common.log_message(
                    "Logging into CentralReach. Attempt #{} failed".format(count),
                    "ERROR",
                )
                print(str(ex))
                self.browser.capture_page_screenshot(
                    os.path.join(
                        os.environ.get("ROBOT_ROOT", os.getcwd()),
                        "output",
                        "Centralreach_login_failed_{}.png".format(count),
                    )
                )
                self.browser.close_browser()
            finally:
                count += 1
