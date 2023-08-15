from RPA.Browser.Playwright import Playwright
import config
from libraries.google_services.sheets_service import GoogleSheets
from libraries.google_services.drive_service import GoogleDrive
from libraries.google_services.gmail_service import Gmail
from libraries.slack_bot import SlackBot
from config import BOT_ACCOUNT, OUTPUT_FOLDER
import datetime
import time
import os
from urllib.parse import urlparse
from libraries.common import log_message


class Quickbooks:

    def __init__(self, login: str, password: str, url: str):
        self.login: str = login
        self.password: str = password
        self.url: str = url
        self.base_url: str = self.get_base_url()

        self.browser = None
        self.drive: GoogleDrive = GoogleDrive(BOT_ACCOUNT)
        self.sheets: GoogleSheets = GoogleSheets(BOT_ACCOUNT)
        self.gmail: Gmail = Gmail(BOT_ACCOUNT)
        self.gmail.move_to_trash_old_mail()
        self.slack: SlackBot = None

    def get_base_url(self):
        parsed_uri = urlparse(self.url)
        base_url = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        return base_url

    def login_to_site(self) -> bool:
        if self.browser is not None:
            self.browser.close_browser()
            self.browser = None

        for i in range(4):
            try:
                self.browser = Playwright(timeout=datetime.timedelta(seconds=45.0))
                # self.browser.open_browser(self.url)
                self.browser.new_page(self.url)

                self.browser.set_viewport_size(1920, 1080)
                self._wait_element('//input[@id="ius-signin-userId-input"]', timeout=30, screenshot=False)
                if self.browser.get_element_state('//input[@id="ius-signin-userId-input"]'):
                    self.browser.fill_text('//input[@id="ius-signin-userId-input"]', self.login)
                else:
                    self.browser.fill_text('//input[@id="ius-userid"]', self.login)

                if self.browser.get_element_state('//input[@id="ius-password"]'):
                    self.browser.fill_text('//input[@id="ius-password"]', self.password)
                    self.browser.click('//button[@id="ius-sign-in-submit-btn"]')
                else:
                    self.browser.click('//button[@id="ius-sign-in-submit-btn"]')
                    self.browser.fill_text('//input[@id="ius-sign-in-mfa-password-collection-current-password"]', self.password)
                    self.browser.click('//input[@id="ius-sign-in-mfa-password-collection-continue-btn"]')

                self._wait_element('//div[text()="Let\'s make sure you\'re you"]', timeout=10, screenshot=False)
                if self.browser.get_element_state('//div[text()="Let\'s make sure you\'re you"]'):
                    self.browser.click('//span[@id="ius-sublabel-mfa-email-otp"]')
                    self.browser.click('//input[@id="ius-mfa-options-submit-btn"]')

                    self.browser.type_text('//input[@id="ius-mfa-confirm-code"]', self.gmail.get_code_from_mail())
                    self.browser.click('//input[@id="ius-mfa-otp-submit-btn"]')
                self._wait_element('//div[@data-automation-id="cm_client_hub_business_name"]')
                if self.browser.get_element_state('//div[@data-automation-id="cm_client_hub_business_name"]'):
                    return True
            except Exception as ex:
                log_message(f'Login failed. Attempt {i}', 'ERROR')
                log_message(str(ex))
                try:
                    self.browser.take_screenshot(os.path.join(OUTPUT_FOLDER, f'Login_failed_Attempt_{i}.png'))
                except Exception as screenshot_error:
                    log_message(str(screenshot_error))
                self.browser.close_browser()
        return False

    def _wait_element(self, xpath: str, timeout: int = 60, screenshot: bool = True) -> None:
        is_success: bool = False
        timer: datetime = datetime.datetime.now() + datetime.timedelta(0, timeout)

        while not is_success and timer > datetime.datetime.now():
            if self.browser.get_element_state(xpath):
                is_success = True
            else:
                time.sleep(5)
        if not is_success and screenshot:
            log_message(f'Element \'{xpath}\' not available', 'ERROR')
            self.browser.take_screenshot(
                os.path.join(
                    OUTPUT_FOLDER,
                    f'Element_not_available_{datetime.datetime.now().strftime("%H_%M_%S")}.png'
                )
            )

    def go_to_client_page(self, client_name: str = 'Gembah') -> None:
        """
        Navigate to client page. Default value 'Gembah'

        :param client_name: Client name
        :return: None
        """
        self.browser.click('//span[text()="GO TO QUICKBOOKS"]')
        self._wait_element(f'//span[text()="{client_name}"]')
        self.browser.click(f'//span[text()="{client_name}"]')
        self._wait_element(f'//div[contains(@class, "companyName") and text()="{client_name}"]')

    def add_invoice(self, customer: str, service: str, description: str, rate: float, processing_fee: bool = False) -> bool:
        """
        Returns the bool if the new invoice was created and sent.

        :param customer: Customer name, column Account from spreadsheet
        :param service: Service name, column Service Type from spreadsheet
        :param description: Description column from spreadsheet
        :param rate: Amount column from spreadsheet
        :param processing_fee: True if column 3% Markup from spreadsheet has value Yes
        :return: status (bool): Bool value indicate if new invoice was created and sent
        """

        self.browser.go_to(f'{self.base_url}/app/homepage')

        self.browser.click('//button[@data-id="global_create_button"]')
        self._wait_element('//a[@data-id="invoice"]')
        self.browser.click('//a[@data-id="invoice"]')

        self._wait_element('//input[@aria-label="Select a customer"]')
        self.browser.type_text('//input[@aria-label="Select a customer"]', customer)

        self._wait_element(f'//span[text()="Add new"]/../span[text()="{customer}"]', timeout=5, screenshot=False)
        self._wait_element(f'//span[@class="mainLabel"]')
        if not self.browser.get_element_state(f'//span[@class="mainLabel"]'):
            self.slack.send_message_service_type_not_found(customer)
            return False

        customers: list = self.browser.get_elements(f'//span[@class="mainLabel"]')
        if len(customers) > 1:
            for i in range(5):
                time.sleep(1)
                customers: list = self.browser.get_elements(f'//span[@class="mainLabel"]')
                if len(customers) == 1:
                    break

        selected: bool = False
        for customer_id in customers:
            if str(self.browser.get_text(customer_id)).strip().lower() == customer.strip().lower():
                self.browser.click(customer_id)
                selected = True
                break
        if not selected:
            self.slack.send_message_service_type_not_found(customer)
            return False

        self.browser.click('//input[@data-automation-id="input-dropdown-terms-sales"]/..//div[contains(@class, "dropDownImage")]')
        self._wait_element('//div[text()="Due on receipt"]')
        self.browser.click('//div[text()="Due on receipt"]')

        self.browser.click('//td[text()="1"]')
        self._wait_element('//input[contains(@id, "ItemComboBox") or @aria-label="ProductService"]')
        self.browser.type_text('//input[contains(@id, "ItemComboBox") or @aria-label="ProductService"]', service)
        self._wait_element(f'//div[@class="name"]/span[text()="{service}" and @class="dijitComboBoxHighlightMatch"]')
        if not self.browser.get_element_state(f'//div[@class="name"]/span[text()="{service}" and @class="dijitComboBoxHighlightMatch"]'):
            self.slack.send_message_service_type_not_found(service)
            return False
        self.browser.click(f'//div[@class="name"]/span[text()="{service}" and @class="dijitComboBoxHighlightMatch"]')

        self.browser.type_text('//textarea[@data-automation-id="input-description-txndetails"]', description)
        self.browser.type_text('//input[@data-automation-id="input-rateField"]', str(rate))

        if processing_fee:
            self.browser.click('//td[text()="2"]')
            self._wait_element('//input[contains(@id, "ItemComboBox")]')
            self.browser.type_text('//input[contains(@id, "ItemComboBox")]', 'Credit Card Processing Fee')

            self._wait_element('//div[@class="description"]/span[text()="Credit Card Processing Fee"]')
            self.browser.click('//div[@class="description"]/span[text()="Credit Card Processing Fee"]')

            self.browser.type_text('//input[@data-automation-id="input-rateField"]', str('%.2f' % (rate / 0.97 - rate)))
        if config.PROD:
            self.browser.click('//button[text()="Save and send"]')
            self._wait_element('//button[text()="Send and close"]')
            self.browser.click('//button[text()="Send and close"]')
        else:
            print('Dev test. The invoice was not saved')
            self.browser.take_screenshot(
                os.path.join(
                    OUTPUT_FOLDER,
                    f'Test_run-customer_{customer}-{datetime.datetime.now().strftime("%H_%M_%S")}.png'
                )
            )
            self.browser.click('//i[@aria-label="Close"]')
        return True

    def _click_batch(self, list_of_xpath: list) -> None:
        for xpath in list_of_xpath:
            self._wait_element(xpath)
            self.browser.click(xpath)

    def check_paid(self, rows: list, columns: list) -> None:
        """
        Check paid invoices on web and compare with spreadsheet.
        If they match - update spreadsheet and send message to Slack channel

        :param rows: Spreadsheet rows
        :param columns: List with column name
        :return: None
        """
        self.browser.go_to(f'{self.base_url}/app/homepage')
        self._click_batch([
            '//span[text()="Sales"]/..',
            '//a[text()="Invoices"]',
            '//th[@data-column-id="date"]',
            '//input[@aria-label="textFieldWrapper" and not(@data-automation-id)]',
            '//div[@value="paid"]',
            '//input[@aria-label="textFieldWrapper" and @data-automation-id="date-dropdown"]',
            '//div[@value="m:3"]',
        ])
        if not self.browser.get_element_state('//th[@data-column-id="date" and contains(@class, "sorted-desc")]'):
            self.browser.click('//th[@data-column-id="date"]')

        self._wait_element('//div[@data-sale-status="PAID"]/../..', timeout=15, screenshot=False)
        paid_rows: list = self.browser.get_elements('//div[@data-sale-status="PAID" or @data-sale-status="DEPOSITED"]/../..')
        if not paid_rows:
            return

        for paid_id in paid_rows:
            try:
                # date: str = str(self.browser.get_text(paid_id + '>> //td[@data-column-id="date"]')).strip().lower()
                customer: str = str(self.browser.get_text(paid_id + '>> //td[@data-column-id="customerName"]')).strip()
                amount: str = str(self.browser.get_text(paid_id + '>> //td[@data-column-id="amount"]')).strip()

                for row in rows[1:]:
                    if len(row) < 6:
                        continue
                    amount_with_tax: float = float(str(row[columns.index('amount')]).replace('$', '').replace(',', ''))
                    if str(row[columns.index('3% markup')]).strip().lower() == 'yes':
                        amount_with_tax += round(amount_with_tax / 0.97 - amount_with_tax, 2)

                    if str(customer.lower() in row[columns.index('account')]).strip().lower() \
                            and round(float(amount.replace('$', '').replace(',', '')), 2) == round(amount_with_tax, 2):

                        if len(row) >= 11:
                            temp_paid_amount: float = float('0' + str(row[columns.index('amount paid')]).replace('$', '').replace(',', ''))
                            if str(row[columns.index('invoice paid')]).strip().lower() == 'yes' and \
                                    round(temp_paid_amount, 2) == round(amount_with_tax, 2):
                                break

                        self.browser.click(paid_id)
                        self._wait_element('//div[text()="Paid"]/..//span[@class="status-date"]')
                        if self.browser.get_element_state('//div[text()="Paid"]/..//span[@class="status-date"]'):
                            paid_date: str = self.browser.get_text('//div[text()="Paid"]/..//span[@class="status-date"]')
                            real_amount: str = amount
                        else:
                            paid_date: str = self.browser.get_text('(//div[text()="Payment received"]/..//span[@class="status-date"])[last()]')
                            real_amount: str = self.browser.get_text('(//div[text()="Payment received"]/..//span[@class="money"])[last()]')
                        self.browser.click('//button[@aria-label="Close"]')

                        if len(row) >= 10:
                            if str(row[columns.index('invoice paid')]).strip().lower() == 'yes' and \
                                    str(row[columns.index('invoice payment date')]).strip().lower() == paid_date:
                                self.sheets.write_to_sheet(
                                    'amount paid',
                                    rows.index(row) + 1,
                                    real_amount.replace('$', '').replace(',', ''),
                                )
                                break
                        self.slack.send_message(
                            f"{self.slack.get_user_tag(row[columns.index('account manager')])} "
                            f"{self.slack.manager}, "
                            f"{row[columns.index('account')]} Invoice of "
                            f"{real_amount} has been paid in Quickbooks"
                        )
                        self.sheets.write_to_sheet(
                            'invoice paid',
                            rows.index(row) + 1,
                            'Yes',
                        )
                        self.sheets.write_to_sheet(
                            'invoice payment date',
                            rows.index(row) + 1,
                            paid_date,
                        )
                        self.sheets.write_to_sheet(
                            'amount paid',
                            rows.index(row) + 1,
                            real_amount.replace('$', '').replace(',', ''),
                        )
                        break
            except Exception as ex:
                log_message('Something went wrong when checking payment')
                log_message(str(ex))
