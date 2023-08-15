from RPA.Browser.Selenium import Selenium
from libraries import common
from RPA.PDF import PDF
from urllib.parse import urlparse
import datetime
import time
import os
import shutil


class CentralReach:

    def __init__(self, credentials: dict):
        self.browser: Selenium = Selenium()
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.login_to_central_reach()
        self.base_url: str = self.get_base_url()

    def get_base_url(self):
        parsed_uri = urlparse(self.url)
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

    def login_to_central_reach(self):
        self.browser.close_all_browsers()
        self.browser.timeout = 45
        self.is_site_available = False
        count = 1
        preferences = {
            'download.default_directory': os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'pdf'),
            'plugins.always_open_pdf_externally': True,
            'download.directory_upgrade': True,
            'download.prompt_for_download': False
        }

        while count <= 3 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.url, preferences=preferences)
                self.browser.set_window_size(1920, 1080)
                self.browser.maximize_browser_window()
                common.wait_element(self.browser, "//input[@type='password']", is_need_screen=False, timeout=10)
                if self.browser.does_page_contain_element("//p[text()='Scheduled Maintenance']"):
                    elem = self.browser.find_element("//p[text()='Scheduled Maintenance']")
                    if elem.is_displayed():
                        common.log_message("Logging into CentralReach failed. Scheduled Maintenance.".format(count), 'ERROR')
                        self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'Centralreach_scheduled_maintenance.png'))
                        return
                common.wait_element(self.browser, "//input[@type='password']", is_need_screen=False)
                self.browser.input_text_when_element_is_visible("//input[@type='text']", self.login)
                self.browser.input_text_when_element_is_visible("//input[@type='password']", self.password)
                self.browser.wait_and_click_button("//button[@class='btn']")
                common.wait_element_and_refresh(self.browser, "//span[text()='Favorites']", is_need_screen=False)
                self.is_site_available = self.browser.does_page_contain_element("//span[text()='Favorites']")
            except:
                common.log_message("Logging into CentralReach. Attempt #{} failed".format(count), 'ERROR')
                self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'Centralreach_login_failed_{}.png'.format(count)))
                self.browser.close_browser()
            finally:
                count += 1

    def filtering_data(self, client_id, start_date, end_date):
        self.browser.go_to(self.base_url + '#billingmanager/billing/?startdate=' + start_date + '&enddate=' + end_date + '&billingLabelIdExcluded=580&billStatus=4&copayStatus=2&invoiceStatus=0&clientId=' + client_id + '&pageSize=500')
        common.wait_element(self.browser, '//a[@contactid=' + client_id + ']')
        if not self.browser.does_page_contain_element('//a[@contactid=' + client_id + ']'):
            common.log_message('Unable to find clientID in CR.', 'ERROR')
            exit(0)

        # get client email
        self.browser.click_element_when_visible('//a[@contactid=' + client_id + ']')
        common.wait_element(self.browser, "//div[text()='Email:']/span")
        client_email = self.browser.get_text("//div[text()='Email:']/span")

        # check all
        common.wait_element(self.browser, "//input[@data-bind='checked: listVm.allSelected']")
        self.browser.click_element_when_visible("//input[@data-bind='checked: listVm.allSelected']")

        return client_email

    @staticmethod
    def check_if_downloaded_and_move(path_to_temp, invoice_number):
        downloaded_files = []
        timer = datetime.datetime.now() + datetime.timedelta(0, 60 * 5)

        while len(downloaded_files) == 0 and timer > datetime.datetime.now():
            time.sleep(1)
            downloaded_files = [f for f in os.listdir(path_to_temp) if os.path.isfile(os.path.join(path_to_temp, f))]
        if len(downloaded_files) == 0:
            raise Exception('Failed to download invoice {}'.format(invoice_number))
        old_invoice_path = os.path.join(path_to_temp, downloaded_files[0])
        new_invoice_path = os.path.join(path_to_temp, '{}.pdf'.format(invoice_number))
        new_invoice_path = shutil.move(old_invoice_path, new_invoice_path)
        return new_invoice_path

    def bulk_generate_invoices(self):
        invoice_number = ''
        invoice_path = ''

        try:
            # click Actions
            common.wait_element(self.browser, "//a[@class='btn btn-default dropdown-toggle']")
            self.browser.click_element_when_visible("//a[@class='btn btn-default dropdown-toggle']")

            # click Bulk-generate Invoices
            common.wait_element(self.browser, "//a[contains(.,'Bulk-generate Invoices')]")
            self.browser.click_element_when_visible("//a[contains(.,'Bulk-generate Invoices')]")

            # click Patient Responsibility Invoice
            common.wait_element(self.browser, "//a[text()='Patient Responsibility Invoice']")
            self.browser.click_element_when_visible("//a[text()='Patient Responsibility Invoice']")

            # Choose Bill from
            common.wait_element(self.browser, '//div[@class="btn-group error"]/button[@class="btn dropdown-toggle width-160 overflow-hidden txt-left"]')
            self.browser.click_element_when_visible('//div[@class="btn-group error"]/button[@class="btn dropdown-toggle width-160 overflow-hidden txt-left"]')
            common.wait_element(self.browser, '//a[@data-bind="click: $parent.chooseBillFrom"]')
            self.browser.click_element_when_visible('//a[@data-bind="click: $parent.chooseBillFrom"]')

            # Print invoice
            common.wait_element(self.browser, "//a[@class='btn btn-primary' and text()[contains(.,'Bulk-Generate')]]")
            self.browser.click_element_when_visible("//a[@class='btn btn-primary' and text()[contains(.,'Bulk-Generate')]]")
            common.wait_element(self.browser, "//a[text()='Click here to print your invoices']", 60 * 3)
            self.browser.click_element_when_visible("//a[text()='Click here to print your invoices']")

            # Go to new tab
            browser_tabs = self.browser.get_window_handles()
            tab_id = self.browser.switch_window(browser_tabs[1])
            self.browser.set_window_size(1920, 1080)

            count = 0
            success = False
            while count < 3 and not success:
                count += 1
                try:
                    if not self.browser.does_page_contain_element("//button[text()='Generate PDF']"):
                        self.browser.reload_page()
                    # Deselect Notes
                    common.wait_element(self.browser, "//a[text()='Columns']")
                    self.browser.click_element_when_visible("//a[text()='Columns']")
                    common.wait_element(self.browser, "//input[@value='notes']")
                    self.browser.unselect_checkbox("//input[@value='notes']")
                    # Go to the From/To
                    common.wait_element(self.browser, "//a[text()='From/To']")
                    self.browser.click_element_when_visible("//a[text()='From/To']")
                    common.wait_element(self.browser, "//input[@value='npinumber']")
                    self.browser.click_element_when_visible("//input[@value='npinumber']")
                    self.browser.unselect_checkbox("//input[@value='npinumber']")
                    self.browser.unselect_checkbox("//input[@value='taxid']")
                    self.browser.unselect_checkbox("//input[@value='fax']")

                    # Click Generate PDF
                    common.wait_element_and_refresh(self.browser, "//button[text()='Generate PDF']")
                    self.browser.click_element_when_visible("//button[text()='Generate PDF']")

                    # Download and get invoice ID
                    common.wait_element(self.browser, '//div[@class="form-panel"]/table/tbody/tr[@data-bind="tooltip"]/td/a[@target="blank"]/i[@class="fa fa-download"]', timeout=60 * 8)
                    self.browser.click_element_when_visible('//div[@class="form-panel"]/table/tbody/tr[@data-bind="tooltip"]/td/a[@target="blank"]/i[@class="fa fa-download"]')
                    success = True
                except Exception as ex:
                    if count > 2:
                        raise ex
                    success = False
                    self.browser.reload_page()
                    common.wait_element(self.browser, "//a[text()='Columns']")
                    common.log_message(str(ex))
                    self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'invoice_processing_failed_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S'))))

            # Download and get invoice ID
            common.wait_element(self.browser, '//tbody[@data-bind="foreach: printList"]/tr[@data-bind="tooltip"]/td/span')
            invoice_number = self.browser.get_text('//tbody[@data-bind="foreach: printList"]/tr[@data-bind="tooltip"]/td/span')
            invoice_path = self.check_if_downloaded_and_move(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'pdf'), invoice_number)

            # Switch back to billing tab
            browser_tabs = self.browser.get_window_handles()
            tab_id = self.browser.switch_window(browser_tabs[0])

            common.wait_element(self.browser, "//div[@class='main-content-body after-fixed-xs']/div/a[text()='Back to billing' and @data-bind='click: cancel']")
            self.browser.click_element_when_visible("//div[@class='main-content-body after-fixed-xs']/div/a[text()='Back to billing' and @data-bind='click: cancel']")

            # Click Bulk-Apply Payments
            common.wait_element(self.browser, "//a[text()='Bulk-Apply Payments']")
            self.browser.click_element_when_visible("//a[text()='Bulk-Apply Payments']")

            # Fill fields
            common.wait_element(self.browser, "//input[@data-bind='datepicker: date']")
            self.browser.input_text("//input[@data-bind='datepicker: date']", datetime.datetime.utcnow().strftime('%m/%d/%Y') + '\ue007')
            self.browser.select_from_list_by_label("//select[@name='payment-type']", 'Invoiced')
            self.browser.input_text('//tr/td[4]/input', 'Invoice ' + invoice_number)
            if self.browser.does_page_contain_element("//td/div/select/option[contains(.,'Primary:')]"):
                self.browser.click_element_when_visible("//td/div/select/option[contains(.,'Primary:')]")

            common.wait_element(self.browser, "//button[text()='Apply Payments']")
            self.browser.click_element_when_visible("//button[text()='Apply Payments']")
            common.wait_element(self.browser, "//span[text()='All payments applied successfully']", timeout=15, is_need_screen=False)
            try:
                is_success = self.browser.find_element("//span[text()='All payments applied successfully']")
                if not is_success.is_displayed():
                    common.log_message('Not all payments applied successfully', 'ERROR')
                    self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'invoice_{}_payments_failed.png'.format(invoice_number)))
            except:
                pass
        except Exception as ex:
            common.log_message('Something went wrong')
            common.log_message(str(ex))
            self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'invoice_{}_processing_failed.png'.format(invoice_number)))
            exit(1)
        return invoice_number, invoice_path

    def update_contact_note(self, client_id, invoice_number):
        self.browser.go_to(self.base_url + '#contacts/details/?id=' + client_id + '&mode=profile&edit=activity')
        self.browser.go_to(self.base_url + '#contacts/details/?id=' + client_id + '&mode=profile&edit=activity')
        self.browser.go_to(self.base_url + '#contacts/details/?id=' + client_id + '&mode=profile&edit=activity')

        common.wait_element(self.browser, "//button[text()='Add New']")
        self.browser.click_element_when_visible("//button[text()='Add New']")
        common.wait_element(self.browser, "//select[@id='activity-type-input']")
        self.browser.select_from_list_by_label("//select[@id='activity-type-input']", 'Billing Note')
        self.browser.input_text_when_element_is_visible("//input[@id='subject']", 'Invoice # ' + invoice_number)
        self.browser.input_text_when_element_is_visible("//input[@data-bind='datepicker: activityDate']", datetime.datetime.utcnow().strftime('%m/%d/%Y') + '\ue007')
        self.browser.click_element("//button[contains(.,'Visible:')]")
        common.wait_element(self.browser, "//a[contains(.,'Me and my co-workers')]")
        self.browser.click_element("//a[contains(.,'Me and my co-workers')]")

        self.browser.click_element("//button[text()='Save Activity']")
