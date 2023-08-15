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


class CentralReach:

    def __init__(self, credentials: dict):
        self.browser: Selenium = Selenium()
        self.browser.timeout = 60
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.path_to_temp: str = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'pdf')
        self.base_url: str = self.get_base_url()
        self.login_to_central_reach()

        self.client_id: str = ''
        self.client_email: str = ''
        self.invoices_path: dict = {}
        self.domo_invoices: list = []

    def get_base_url(self) -> str:
        parsed_uri = urlparse(self.url)
        base_url: str = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

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
                common.wait_element(self.browser, "//input[@type='password']", is_need_screen=False, timeout=10)
                if self.browser.does_page_contain_element("//p[text()='Scheduled Maintenance']"):
                    if self.browser.find_element("//p[text()='Scheduled Maintenance']").is_displayed():
                        common.log_message("Logging into CentralReach failed. Scheduled Maintenance.".format(count), 'ERROR')
                        self.browser.capture_page_screenshot(
                            os.path.join(
                                os.environ.get("ROBOT_ROOT", os.getcwd()),
                                'output',
                                'Centralreach_scheduled_maintenance.png')
                        )
                        return
                common.wait_element(self.browser, "//input[@type='password']", is_need_screen=False)
                self.browser.input_text_when_element_is_visible("//input[@type='text']", self.login)
                self.browser.input_text_when_element_is_visible("//input[@type='password']", self.password)
                self.browser.click_button_when_visible("//button[@class='btn']")
                if self.browser.does_page_contain_element('//div[@class="loginError"]/div[text()="There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support"]'):
                    elem = self.browser.find_element('//div[@class="loginError"]/div[text()="There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support"]')
                    if elem.is_displayed():
                        common.log_message("Logging into CentralReach failed. There was an unexpected problem signing in.".format(count), 'ERROR')
                        raise Exception("There was an unexpected problem signing in. If you keep seeing this, please contact CentralReach Support")
                common.wait_element_and_refresh(self.browser, "//span[text()='Favorites']", is_need_screen=False)
                self.is_site_available = self.browser.does_page_contain_element("//span[text()='Favorites']")
            except Exception as ex:
                common.log_message("Logging into CentralReach. Attempt #{} failed".format(count), 'ERROR')
                print(str(ex))
                self.browser.capture_page_screenshot(
                    os.path.join(
                        os.environ.get("ROBOT_ROOT", os.getcwd()),
                        'output',
                        'Centralreach_login_failed_{}.png'.format(count)
                    )
                )
                self.browser.close_browser()
            finally:
                count += 1

    def close_specific_windows(self, xpath: str):
        try:
            if self.browser.does_page_contain_element(xpath):
                elements: list = self.browser.find_elements(xpath)
                for element in elements:
                    try:
                        if element.is_displayed():
                            common.log_message('A pop-up appeared and the bot closed it. Please validate the screenshot of the pop-up in the artifacts.', 'ERROR')
                            self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'Pop_up_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))
                            element.click()
                            self.browser.wait_until_element_is_not_visible('({})[{}]'.format(xpath, elements.index(element) + 1))
                    except:
                        time.sleep(1)
        except:
            pass

    def wait_element(self, xpath: str, timeout: int = 60, is_need_screen: bool = True) -> None:
        is_success = False
        timer = datetime.datetime.now() + datetime.timedelta(0, timeout)

        while not is_success and timer > datetime.datetime.now():
            self.close_specific_windows('//button[contains(@id, "pendo-close-guide")]')

            if self.browser.does_page_contain_element(xpath):
                try:
                    elem = self.browser.find_element(xpath)
                    is_success = elem.is_displayed()
                except:
                    time.sleep(1)
        if not is_success and is_need_screen:
            common.log_message('Element \'{}\' not available'.format(xpath), 'ERROR')
            self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'Element_not_available_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))

    def get_client_email(self) -> None:
        client_email: str = ''

        self.browser.go_to(f'{self.base_url}#contacts/details/?id={self.client_id}')
        common.wait_element(self.browser, "//h2[text()='Unable to load this contact']", 1, False)
        if not self.browser.does_page_contain_element("//h2[text()='Unable to load this contact']"):
            try:
                common.wait_element_and_refresh(self.browser, "//span[text()='Profile']")
                self.browser.click_element_when_visible("//span[text()='Profile']")
                common.wait_element_and_refresh(self.browser, "//h4[text()='Basics']")
                self.browser.click_element_when_visible("//h4[text()='Basics']")
                common.wait_element_and_refresh(self.browser, "//input[@id='email']")
                client_email = self.browser.get_value("//input[@id='email']")
            except:
                self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', f'client_id_{self.client_id}_processing_failed.png'))
        if len(client_email) == 0:
            common.log_message("Can't get the client email from the Central Reach site", 'ERROR')
            exit(1)

        list_of_email = client_email.strip().split()
        list_of_email = list(filter(None, list_of_email))
        self.client_email = str.join(';', list_of_email)
        common.log_message('Client email is {}'.format(client_email))

    def check_if_downloaded_and_move(self, invoice_number: str) -> str:
        downloaded_files: list = []
        timer: datetime = datetime.datetime.now() + datetime.timedelta(0, 60 * 5)

        while timer > datetime.datetime.now():
            time.sleep(1)
            downloaded_files = [f for f in os.listdir(self.path_to_temp) if os.path.isfile(os.path.join(self.path_to_temp, f))]
            if len(downloaded_files) > 0 and downloaded_files[0].endswith('.pdf'):
                time.sleep(1)
                break
        if len(downloaded_files) == 0:
            raise Exception('Failed to download invoice {}'.format(invoice_number))
        old_invoice_path = os.path.join(self.path_to_temp, downloaded_files[0])
        new_invoice_path = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'output', f'{invoice_number}.pdf')
        new_invoice_path = shutil.move(old_invoice_path, new_invoice_path)
        return new_invoice_path

    @staticmethod
    def read_pdf(path_to_pdf: str) -> (str, str):
        invoice_col = -1
        amount_col = -1
        invoice_number_from_pdf = ''
        invoice_amount_from_pdf = ''
        count = 0
        error = True

        while count < 3 and error is True:
            count += 1
            error = False
            try:
                pdf_reader = PDF()
                pdf_reader.parse_pdf(path_to_pdf)
                try:
                    first_page = pdf_reader.rpa_pdf_document.get_page(1)
                    for line in range(len(first_page.content) - 2):
                        if 'Invoice Number:' in first_page.content[line].text:
                            tmp_col = first_page.content[line].text.split('\n')
                            for col in tmp_col:
                                if 'Invoice Number:'.lower() == col.strip().lower():
                                    invoice_col = tmp_col.index(col)
                                elif 'Amount Due:'.lower() == col.strip().lower():
                                    amount_col = tmp_col.index(col)
                            tmp_val = first_page.content[line + 1].text.split('\n')
                            invoice_number_from_pdf = tmp_val[invoice_col]
                            invoice_amount_from_pdf = tmp_val[amount_col]
                except Exception as e:
                    common.log_message('Error parsing: {}. Potential reason: {}'.format(basename(path_to_pdf), str(e)), 'ERROR')
                pdf_reader.close_all_pdf_documents()
            except Exception as e:
                error = True
                common.log_message('Fatal error parsing: {}. Potential reason: {}'.format(basename(path_to_pdf), str(e)), 'ERROR')
                try:
                    exc_info = sys.exc_info()
                    traceback.print_exception(*exc_info)
                    del exc_info
                except:
                    pass
        return invoice_number_from_pdf, invoice_amount_from_pdf

    def download_invoices(self) -> None:
        not_found_invoices: int = 0

        self.browser.set_window_size(3840, 2160)
        if len(self.domo_invoices) > 1:
            common.log_message('Starting to download invoices: {}'.format(str.join(', ', self.domo_invoices)))
        for invoice_number in self.domo_invoices:
            try:
                common.log_message('Starting to download invoice {}'.format(invoice_number))

                self.browser.go_to(f"{self.base_url}#billingmanager/invoices/?invoiceId={invoice_number}")
                common.wait_element(self.browser, "//div[text()='" + invoice_number + "']")
                if self.browser.does_page_contain_element("//div[text()='" + invoice_number + "']"):
                    common.wait_element(self.browser, "//a[text()='Actions ']", 30)
                    self.browser.click_element_when_visible("//a[text()='Actions ']")
                    common.wait_element(self.browser, "//a[text()='Download']", 15)
                    if self.browser.does_page_contain_element("//a[text()='Download']"):
                        elem = self.browser.find_element("//a[text()='Download']")
                        if not elem.is_displayed():
                            self.browser.click_element_when_visible("//a[text()='Actions ']")
                            common.wait_element(self.browser, "//a[text()='Download']", 15)
                    self.browser.click_element_when_visible("//a[text()='Download']")
                    path_to_invoice = self.check_if_downloaded_and_move(invoice_number)
                    number_from_pdf, amount_from_pdf = self.read_pdf(path_to_invoice)
                    if invoice_number == number_from_pdf:
                        self.invoices_path[invoice_number] = {
                            'path': path_to_invoice,
                            'amount': amount_from_pdf
                        }
                        common.log_message('Invoice {} downloaded successfully'.format(invoice_number))
                    else:
                        shutil.move(path_to_invoice, os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', f'Invoice_{invoice_number}.pdf'))
                        common.log_message("Download invoice {} has different number inside PDF {}. The file will be added to the artifacts. Please re-check it.".format(invoice_number, number_from_pdf), 'ERROR')
                        not_found_invoices += 1
                else:
                    common.log_message('Unable to locate Invoice {}. Please check to see if this invoice exists in Central Reach.'.format(invoice_number), 'ERROR')
                    not_found_invoices += 1
            except Exception as e:
                common.log_message('Unable to locate Invoice {}. Please check to see if this invoice exists in Central Reach.'.format(invoice_number), 'ERROR')
                common.log_message("Can not download invoice {}. Reason: {}".format(invoice_number, str(e)), 'ERROR')
                not_found_invoices += 1
                self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'invoice_{}_processing_failed.png'.format(invoice_number)))
                try:
                    exc_info = sys.exc_info()
                    traceback.print_exception(*exc_info)
                    del exc_info
                except:
                    pass

        if not_found_invoices > 0:
            exit(1)

    def update_billing_manager(self):

        for invoice_number in self.domo_invoices:
            common.log_message('Filtering billing data by invoice number {}'.format(invoice_number))
            # I don't know why, but it doesn't work sometimes
            self.browser.go_to(f'{self.base_url}#billingmanager/billing/?invoiceId=' + invoice_number)
            self.browser.go_to(f'{self.base_url}#billingmanager/billing/?invoiceId=' + invoice_number)
            self.browser.go_to(f'{self.base_url}#billingmanager/billing/?invoiceId=' + invoice_number)

            common.wait_element(self.browser, "//em[text()='Invoice: Invoice #: " + invoice_number + "']")
            if self.browser.does_page_contain_element("//em[text()='Invoice: Invoice #: " + invoice_number + "']"):
                common.wait_element(self.browser, "//input[@data-bind='checked: listVm.allSelected']")
                self.browser.click_element_when_visible("//input[@data-bind='checked: listVm.allSelected']")
                self.browser.click_element_when_visible("//a[text()='Bulk-Apply Payments']")

                common.wait_element(self.browser, "//input[@data-bind='datepicker: date']")
                self.browser.input_text_when_element_is_visible("//input[@data-bind='datepicker: date']", datetime.datetime.now().strftime('%m/%d/%Y') + '\ue007')
                self.browser.select_from_list_by_label("//select[@name='payment-type']", 'Activity')
                self.browser.input_text_when_element_is_visible("//input[@data-bind='value: notes']", 'AleBot sent fu on invoice {}'.format(invoice_number))

                if self.browser.does_page_contain_element("//td/div/select/option[text()[contains(.,'Credit Card')]]"):
                    self.browser.click_element_when_visible("//td/div/select/option[text()[contains(.,'Credit Card')]]")

                self.browser.click_element_when_visible("//button[text()='Apply Payments']")

                common.wait_element(self.browser, "//span[text()='All payments applied successfully']", timeout=15, is_need_screen=False)
                try:
                    is_success = self.browser.find_element("//span[text()='All payments applied successfully']")
                    if not is_success.is_displayed():
                        common.log_message('Not all payments applied successfully', 'ERROR')
                        self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'invoice_{}_payments_failed.png'.format(invoice_number)))
                except:
                    pass
            else:
                common.log_message('There is no data for the invoice number {}'.format(invoice_number), 'ERROR')
                exit(1)

    def update_contact_note(self):
        self.browser.go_to(f'{self.base_url}#contacts/details/?id={self.client_id}&mode=profile&edit=activity')
        common.wait_element(self.browser, "//button[text()='Add New']")
        self.browser.click_element_when_visible("//button[text()='Add New']")
        common.wait_element(self.browser, "//select[@id='activity-type-input']")
        self.browser.select_from_list_by_label("//select[@id='activity-type-input']", 'Billing Note')

        if len(self.domo_invoices) == 1:
            self.browser.input_text_when_element_is_visible("//input[@id='subject']", 'AleBot sent fu on invoice {}'.format(self.domo_invoices[0]))
        else:
            self.browser.input_text_when_element_is_visible("//input[@id='subject']", 'AleBot sent fu on invoices {} and {}'.format(str.join(', ', self.domo_invoices[0:-1]), self.domo_invoices[-1]))

        self.browser.input_text_when_element_is_visible("//input[@data-bind='datepicker: activityDate']", datetime.datetime.now().strftime('%m/%d/%Y') + '\ue007')

        self.browser.click_element("//button[text()[contains(.,'Visible:')]]")
        common.wait_element(self.browser, "//a[text()[contains(.,'Me and my co-workers')]]")
        self.browser.click_element("//a[text()[contains(.,'Me and my co-workers')]]")

        self.browser.click_element("//button[text()='Save Activity']")
