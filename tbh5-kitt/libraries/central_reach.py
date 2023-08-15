from RPA.Browser.Selenium import Selenium
from libraries import common
import datetime
import time
import re
import os
import traceback
import sys
import numpy
from libraries.excel import ExcelInterface
from libraries.waystar import WayStar
from libraries.central_reach_core import CentralReachCore
from libraries.central_reach_requests import CentralReachRequests
from libraries.google_drive import GoogleDrive
from libraries.pdf import PDF
from libraries.eob import EOB, Adjustment, ACNT, Service


class CentralReach(CentralReachCore):
    cash_receipts: ExcelInterface = None
    waystar: WayStar = None
    lockbox_remit_other: ExcelInterface = None
    headers_index: dict = {}

    provider: str = 'Trumpet Behavioral Health'
    filter_name = 'Patient Responsibility'
    list_of_non_insurance = ['None', 'School District', 'California Regional Center', 'Private Pay']

    def find_timesheet_by_client_id(self, client_id: str, date_of_service: datetime):
        date: str = date_of_service.strftime("%Y-%m-%d")
        self.browser.go_to(f'{self.base_url}/#billingmanager/billing/?startdate={date}&enddate={date}&clientId={client_id}&billStatus=0')
        self.wait_element(f'//em[contains(., "{client_id}")]')

    def find_timesheet_by_invoice_id(self, invoice_id: str):
        self.browser.go_to(self.base_url)
        self.browser.go_to(f'{self.base_url}/#billingmanager/billing/?invoiceId={invoice_id}')
        self.wait_element_and_refresh(f'//em[contains(., "{invoice_id}")]', timeout=60*3)

    def find_timesheet_by_claim_id(self, claim_id: str):
        self.browser.go_to(self.base_url)
        self.browser.go_to(f'{self.base_url}/#billingmanager/billing/?claimId={claim_id}')
        self.wait_element_and_refresh(f'//em[contains(., "{claim_id}")]')

    def fb_modifications(self, date_of_service: datetime, insurance_name: str):
        unknowns_insurance_id: str = '177374'

        for i in range(3):
            try:
                self.browser.go_to(f'{self.base_url}/#billingmanager/timesheeteditor/?newentry=true')
                self.wait_element_and_refresh('//div[text()="New Timesheet"]')

                self.browser.input_text_when_element_is_visible('//label[text()="Client name"]/../div/input', unknowns_insurance_id)
                self.wait_and_click(f'//div[contains(., "{unknowns_insurance_id}") and @role="button"]')
                self.wait_element(f'//h2[contains(., "{unknowns_insurance_id}")]', 30, False)
                if not self.browser.does_page_contain_element(f'//h2[contains(., "{unknowns_insurance_id}")]'):
                    self.wait_and_click(f'//div[contains(., "{unknowns_insurance_id}") and @role="button"]')
                self.wait_element(f'//h2[contains(., "{unknowns_insurance_id}")]')

                self.browser.input_text_when_element_is_visible('//label[text()="Provider"]/..//input', self.provider)
                self.wait_and_click(f'//div[contains(., "{self.provider}") and @role="option"]')

                self.browser.input_text_when_element_is_visible('//label[text()="Date of service"]/..//input', date_of_service.strftime('%m-%d-%Y') + '\ue007')

                self.wait_and_click('//ul[contains(@class, "nav")]/li/a[contains(., "Service Codes")]')
                self.browser.execute_javascript('window.scrollBy(0, 42000)')  # Nothing special, just want to be sure that bot will at the bottom of the page
                self.wait_and_click('//span[text()="Unapplied Credits"]')
                self.wait_element('//div[text()="Unapplied Credits"]')

                self.wait_element('//input[@placeholder="Time From"]', 5, False)
                if not self.browser.does_page_contain_element('//input[@placeholder="Time From"]'):
                    if self.browser.does_page_contain_element('//span[text()="back"]'):
                        self.browser.execute_javascript('window.scrollBy(0, -42000)')
                        self.browser.click_element_when_visible('//span[text()="back"]')
                self.wait_element('//input[@placeholder="Time From"]')
                self.browser.input_text_when_element_is_visible('//input[@placeholder="Time From"]', '08:00 AM')
                self.browser.input_text_when_element_is_visible('//input[@placeholder="Time To"]', '08:30 AM')

                insurances: list = self.browser.find_elements('//option[text()="Choose a Payor(optional)"]/../option')
                insurances[0].click()  # Select default option "Choose a Payor(optional)"
                for insurance in insurances:
                    if insurance_name.strip().lower() in str(insurance.text).strip().lower():
                        insurance.click()
                        break
                self.browser.select_from_list_by_value('//label[text()="Are you editing this time sheet on behalf of another team member?"]/..//select', '0')
                self.wait_and_click('//span[text()="SUBMIT"]/../../button[contains(@class, "MuiButton-containedPrimary")]')
                break
            except Exception as ex:
                print(f'fb_modifications(): retry {i}. {str(ex)}')

        time.sleep(.5)
        self.find_timesheet_by_client_id(unknowns_insurance_id, date_of_service)

    def get_payments_data(self, check_number: str, payment_type: str, date: datetime) -> dict:
        if not self.headers_index:
            self.headers_index = self.find_header_index(
                ['client', 'date', 'payor', 'service/auth', 'agreed', 'pr amt.', 'paid', 'owed']
            )

        rows: list = self.browser.find_elements('//tr[contains(@id, "billing-grid-row-")]')
        timesheets_data: dict = {}
        for row in rows:
            timesheet_id: str = row.get_attribute('id')
            timesheet_id = timesheet_id.split('-')[-1].strip()
            service_code: str = row.find_element_by_xpath('td/a[@data-title-bind="procedureCodeString"]').text
            service_code = service_code.split(':')[0].strip()
            timesheets_data[timesheet_id] = service_code

        payments_data: dict = {}
        payments_data_temp: list = []
        for timesheet_id in timesheets_data:
            self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/a[@data-title="Click to view or add payments"]')
            try:
                self.browser.click_element_when_visible(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/a[@data-title="Click to view or add payments"]')
            except:
                self.browser.execute_javascript('window.scrollBy(0, 42)')
                self.browser.click_element_when_visible(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/a[@data-title="Click to view or add payments"]')

            self.wait_element(f'//tr[@id="billing-grid-row-{timesheet_id}"]/following-sibling::tr[1]')
            self.wait_element(f'//tr[@id="billing-grid-row-{timesheet_id}"]/following-sibling::tr[1]//span[text()=" Payments"][last()]/span', timeout=5, is_need_screen=False)
            payment_count: str = self.browser.get_text(f'//tr[@id="billing-grid-row-{timesheet_id}"]/following-sibling::tr[1]//span[text()=" Payments"][last()]/span')

            if payment_count != '0':

                payments: list = self.browser.find_elements('//tr[@data-paymentid]')
                for payment in payments[len(payments_data_temp):]:
                    payment_date_str: str = payment.find_element_by_xpath('td/span[@data-bind="text: dateDisplay()"]').text
                    payment_date: datetime = datetime.datetime.strptime(payment_date_str, '%m/%d/%y')
                    payment_amount: float = float(str(payment.find_element_by_xpath('td/span[contains(@data-bind, "amount()")]').text).strip().replace(',', ''))
                    payment_type_from_web: str = payment.find_element_by_xpath('td/span[@data-bind="text: paymentTypeDescription()"]').text
                    check_number_from_web: str = payment.find_element_by_xpath('td/a[contains(@data-bind, "claimPaymentId()")]').text
                    if not check_number_from_web:
                        check_number_from_web: str = payment.find_element_by_xpath('td/span[contains(@data-bind, "claimPaymentId()")]').text
                    payments_data_temp.append(payment.text)

                    if payment_type_from_web.strip().lower() == payment_type.lower() and\
                            payment_date.strftime("%m/%d/%y") == date.strftime("%m/%d/%y") and\
                            check_number_from_web.strip(' 0').lower() == check_number.strip(' 0').lower():
                        if timesheet_id not in payments_data:
                            payments_data[timesheet_id] = []
                        payments_data[timesheet_id].append(
                            Service(timesheets_data[timesheet_id],
                                    payment_date,
                                    0,
                                    0,
                                    payment_amount,
                                    {}
                                    )
                        )
            self.browser.click_element_when_visible(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/a[@data-title="Click to view or add payments"]')
            self.browser.wait_until_element_is_not_visible('(//span[text()=" Payments"])[last()]/span')
        return payments_data

    @staticmethod
    def get_matrix_by_code(payments_data: dict) -> dict:
        matrix_by_code: dict = {}
        max_len: int = 0
        only_positive: dict = {}
        only_negative: dict = {}

        for payments in payments_data.values():
            temp_list: list = []
            for payment in payments:
                temp_list.append(payment.prov_pd)
            # for some specific cases - positive
            for payment in payments:
                if payment.code not in only_positive:
                    only_positive[payment.code] = 0
                if payment.prov_pd > 0:
                    only_positive[payment.code] += payment.prov_pd
                    break
            # for some specific cases - negative
            for payment in payments:
                if payment.code not in only_negative:
                    only_negative[payment.code] = 0
                if payment.prov_pd < 0:
                    only_negative[payment.code] += payment.prov_pd
                    break

            code: str = payments[0].code
            if code not in matrix_by_code:
                matrix_by_code[code] = []
            if len(temp_list) > max_len:
                max_len = len(temp_list)

            matrix_by_code[code].append(temp_list.copy())

        for code, matrix in matrix_by_code.items():
            for row in matrix:
                while len(row) < max_len:
                    row.append(row[0])

        matrix_result: dict = {}
        for code in matrix_by_code:
            temp = matrix_by_code[code]
            matrix_result[code] = (numpy.array(temp).cumsum()).tolist()
            matrix_result[code] += (numpy.array(temp).sum(axis=0)).tolist()
            matrix_result[code].append(only_positive[code])
            matrix_result[code].append(only_negative[code])

        # for other specific cases
        for payments in payments_data.values():
            for payment in payments:
                matrix_result[payment.code].append(payment.prov_pd)

        # Do not ask. For handle a lot of specific cases
        count_of_processed: int = 0
        for payments_first in payments_data.values():
            for payment_first in payments_first:
                for payments_second in payments_data.values():
                    if count_of_processed <= list(payments_data.values()).index(payments_second):
                        continue
                    for payment_second in payments_second:
                        if payment_first.code == payment_second.code:
                            matrix_result[payment_first.code].append(round(payment_first.prov_pd + payment_second.prov_pd, 2))
            count_of_processed += 1

        # just to remove duplicates
        for code in matrix_result:
            matrix_result[code] = list(set(matrix_result[code]))

        return matrix_result

    def check_payments(self, check_number: str, payment_type: str, date: datetime, acnt: ACNT) -> bool:
        payments_data: dict = self.get_payments_data(check_number, payment_type, date)
        if not payments_data:
            print(f'_no payments_data in check_payments()')
            return False
        payments_by_service: dict = self.get_matrix_by_code(payments_data)

        is_valid: bool = False
        for service in acnt.services:
            is_valid = False
            if service.code in payments_by_service:
                for amount in payments_by_service[service.code]:
                    if round(service.prov_pd, 2) == round(amount, 2):
                        is_valid = True
                        break
                if not is_valid:
                    break
            else:
                is_valid = True
        return is_valid

    def check_payments_adjustment(self, check_number: str, payment_type: str, date: datetime, adjustment: Adjustment) -> bool:
        payments_data: dict = self.get_payments_data(check_number, payment_type, date)
        if not payments_data:
            print(f'_no payments_data in check_payments_adjustment()')
            return False
        # payments_by_service: dict = self.get_payments_by_service(payments_data)

        total: float = 0.0
        for services in payments_data.values():
            for service in services:
                total += service.prov_pd

        return round(total * -1, 2) == round(adjustment.amount, 2)

    def pre_bulk_apply_payments(self, payment_type: str, check_number: str, notes: str) -> None:
        self.wait_and_click('//input[@data-bind="checked: listVm.allSelected"]')
        self.wait_and_click('//a[text()="Bulk-Apply Payments"]')

        self.wait_element('//input[@data-bind="datepicker: date"]')
        self.browser.input_text_when_element_is_visible("//input[@data-bind='datepicker: date']", self.cash_receipts.current_valid_date.strftime('%m/%d/%Y') + '\ue007')

        self.browser.select_from_list_by_label("//select[@name='payment-type']", payment_type)

        count_of_input: int = len(self.browser.find_elements('//input[contains(@data-bind, "bulkPaymentAmount")]'))
        for i in range(1, count_of_input + 1):
            self.browser.input_text_when_element_is_visible(f'(//input[contains(@data-bind, "bulkPaymentAmount")])[{i}]', '0')

        self.browser.input_text_when_element_is_visible('//input[contains(@data-bind, "reference")]', check_number)
        self.browser.input_text_when_element_is_visible("//input[@data-bind='value: notes']", notes)

    def bulk_apply_payments_adjustment(self, acnt: ACNT, adjustment: Adjustment or None = None) -> float:
        total_amount: float = 0.0

        bulk_payment_amounts: list = self.browser.find_elements('//input[contains(@data-bind, "bulkPaymentAmount")]')
        if len(bulk_payment_amounts) == 1:
            self.browser.input_text_when_element_is_visible('//input[contains(@data-bind, "bulkPaymentAmount")]', str(adjustment.amount * -1))
            total_amount += adjustment.amount * -1
        else:
            for service in acnt.services:

                services: list = self.browser.find_elements(f'//span[contains(., "{service.code}")]')
                if len(services) == 1:
                    self.browser.input_text_when_element_is_visible(f'//span[contains(., "{service.code}")]/../..//input[contains(@data-bind, "bulkPaymentAmount")]', str(service.prov_pd))
                    total_amount += service.prov_pd
                else:
                    amounts_paid: list = self.browser.find_elements(f'//span[contains(., "{service.code}")]/../..//td[contains(@data-bind, "amountPaid")]')
                    amount_paid: float = .0
                    for a in amounts_paid:
                        amount_paid += round(float(str(a.text).replace(',', '')), 2)

                    amounts_owed: list = self.browser.find_elements(f'//span[contains(., "{service.code}")]/../..//span[contains(@data-bind, "amountOwed")]/..')
                    amount_owed: float = .0
                    for a in amounts_owed:
                        amount_owed += round(float(str(a.text).replace(',', '')), 2)

                    if round(amount_paid * -1, 2) == round(service.prov_pd, 2):
                        for i in range(1, len(amounts_paid) + 1):
                            temp_amount: float = round(float(str(amounts_paid[i - 1].text).replace(',', '')), 2) * -1
                            self.browser.input_text_when_element_is_visible(f'(//span[contains(., "{service.code}")]/../..//input)[{i}]', str(temp_amount))
                            total_amount += temp_amount
                    elif round(amount_owed, 2) == round(service.prov_pd, 2):
                        for i in range(1, len(amounts_owed) + 1):
                            temp_amount: float = round(float(str(amounts_owed[i - 1].text).replace(',', '')), 2) * -1
                            self.browser.input_text_when_element_is_visible(f'(//span[contains(., "{service.code}")]/../..//input)[{i}]', str(temp_amount))
                            total_amount += temp_amount
                    else:
                        self.browser.input_text_when_element_is_visible(f'//span[contains(., "{service.code}")]/../..//input[contains(@data-bind, "bulkPaymentAmount")]', str(service.prov_pd))
                        total_amount += service.prov_pd
        return round(total_amount, 2)

    def populate_payments_non_adjustment(self, service: Service, second: bool) -> float:
        pr_amount: float = 0.0
        for amount in service.obligations.values():
            pr_amount += amount
        pr_amount = round(pr_amount, 2)

        amounts_charges: list = self.browser.find_elements(f'//span[contains(., "{service.code}")]/../..//span[contains(@data-bind, "clientCharges")]/..')
        amounts_owed: list = self.browser.find_elements(f'//span[contains(., "{service.code}")]/../..//span[contains(@data-bind, "amountOwedAgreed")]/..')
        total_amount_owed: float = .0
        total_amount_charges: float = .0
        list_of_valid: list = []
        for amount in amounts_owed:
            i: int = amounts_owed.index(amount)
            value_from_web: str = self.browser.get_value(f'(//span[contains(., "{service.code}")]/../..//input)[{i + 1}]')
            if value_from_web and value_from_web != '0':
                continue

            list_of_valid.append(i + 1)
            temp_amount_owed: float = round(float(str(amount.text).replace(',', '')), 2)
            temp_amount_charges: float = round(float(str(amounts_charges[i].text).replace(',', '')), 2)
            total_amount_owed += temp_amount_owed
            total_amount_charges += temp_amount_charges
            if round(temp_amount_owed, 2) == round(service.prov_pd + pr_amount, 2) \
                    and round(temp_amount_charges, 2) == round(service.allowed, 2):
                self.browser.input_text_when_element_is_visible(f'(//span[contains(., "{service.code}")]/../..//input)[{i + 1}]', str(service.prov_pd))
                service.populated = True
                return service.prov_pd

        if round(total_amount_owed, 2) == round(service.prov_pd + pr_amount, 2) \
                and round(total_amount_charges, 2) == round(service.allowed, 2):
            for i in list_of_valid:
                temp_amount_str: str = str(amounts_owed[i - 1].text).replace(',', '')
                if pr_amount:
                    temp_amount_str = str(float(temp_amount_str) - pr_amount)
                    pr_amount = 0.0
                self.browser.input_text_when_element_is_visible(f'(//span[contains(., "{service.code}")]/../..//input)[{i}]', temp_amount_str)
            service.populated = True
            return service.prov_pd
        elif second:
            temp_prov_pd: float = service.prov_pd
            input_fields: list = self.browser.find_elements(f'//span[contains(., "{service.code}")]/../..//input')
            for input_field in input_fields:
                value_from_web: str = input_field.get_property('value')
                if value_from_web and value_from_web != '0':
                    continue
                index: int = input_fields.index(input_field) + 1
                amount_owed_str: str = self.browser.get_text(f'(//span[contains(., "{service.code}")]/../..//span[contains(@data-bind, "amountOwedAgreed")]/..)[{index}]')
                amount_owed: float = round(float(amount_owed_str.replace(',', '')), 2)
                if temp_prov_pd > amount_owed and index != len(input_fields):
                    self.browser.input_text_when_element_is_visible(f'(//span[contains(., "{service.code}")]/../..//input)[{index}]', str(amount_owed))
                    temp_prov_pd -= amount_owed
                else:
                    self.browser.input_text_when_element_is_visible(f'(//span[contains(., "{service.code}")]/../..//input)[{input_fields.index(input_field) + 1}]', str(round(temp_prov_pd, 2)))
                    temp_prov_pd = 0.0
                    break
            if temp_prov_pd == 0.0:
                service.populated = True
            return service.prov_pd - temp_prov_pd
        return 0.0

    def bulk_apply_payments_non_adjustment(self, acnt: ACNT) -> float:
        total_amount: float = 0.0

        for service in acnt.services:
            print(service)

            if service.prov_pd == 0.0:
                service.populated = True
                continue

            services: list = self.browser.find_elements(f'//span[contains(., "{service.code}")]')
            if len(services) == 0:
                service.populated = True
                continue
            elif len(services) == 1:
                self.browser.input_text_when_element_is_visible(f'//span[contains(., "{service.code}")]/../..//input[contains(@data-bind, "bulkPaymentAmount")]', str(service.prov_pd))
                total_amount += service.prov_pd
                service.populated = True
            else:
                total_amount += self.populate_payments_non_adjustment(service, False)
        for service in acnt.services:
            if not service.populated:
                total_amount += self.populate_payments_non_adjustment(service, True)
        return round(total_amount, 2)

    def post_bulk_apply_payments(self, insurance_name: str) -> None:
        self.browser.click_element("//input[@data-bind='value: notes']")
        insurances: list = self.browser.find_elements('//select[contains(@data-bind, "client.payorsUi")]/option')
        for insurance in insurances:
            if insurance_name.strip().lower() in str(insurance.text).strip().lower():
                insurance.click()
                break

        self.browser.click_element_when_visible("//button[text()='Apply Payments']")
        self.wait_element('//span[text()="All payments applied successfully"]', timeout=15, is_need_screen=False)
        try:
            if not self.browser.find_element('//span[text()="All payments applied successfully"]').is_displayed():
                common.log_message('Not all payments applied successfully', 'ERROR')
        except:
            pass
        self.browser.click_element_when_visible('//a[text()="Back to billing" and @data-click="cancel"]')

    def interest_adjustment(self, eft_number: str, insurance_name: str, adjustment: Adjustment) -> float:
        client: str = 'Interest Payments'
        service_code: str = 'Unapplied Credits'

        self.browser.go_to(f'{self.base_url}/#claims/eralist/?checknumber={eft_number}')

        self.wait_element(f'//a[text()="{eft_number}"]')
        if self.browser.does_page_contain_element('//span[text()="No Rows To Show"]'):
            return 0.0

        payment_id: str = self.browser.get_text('//a[@data-title="Open this ERA" and contains(@href, "paymentId")]/span')
        link: str = self.browser.get_element_attribute('//a[@data-title="Open this ERA" and contains(@href, "paymentId")]', 'href')
        self.browser.go_to(link)
        self.wait_element(f'//a[text()="{payment_id}"]')

        if self.browser.does_page_contain_element('//a[text()="Adjustments"]'):
            self.browser.click_element_when_visible('//a[text()="Adjustments"]')
            if self.browser.does_page_contain_element('//span[text()="L6 - Interest Owed"]/../..//span[text()="Set billing info"]'):
                self.wait_and_click('//span[text()="L6 - Interest Owed"]/../..//span[text()="Set billing info"]')

                self.wait_element('//input[@placeholder="Search contact"]')
                self.browser.input_text_when_element_is_visible('//label[text()="Client"]/..//input', client)
                self.wait_and_click(f'//div[contains(., "{client}") and @role="option"]')

                self.wait_element('//select[@class="form-control"]')
                insurances: list = self.browser.find_elements('//select[@class="form-control"]/option')
                for insurance in insurances:
                    if insurance_name.lower() in str(insurance.text).lower():
                        insurance.click()
                        break

                self.browser.input_text_when_element_is_visible('//label[text()="Provider"]/..//input', self.provider)
                self.wait_and_click(f'//div[contains(., "{self.provider}") and @role="option"]')
                self.browser.input_text_when_element_is_visible('//label[text()="Service Code"]/..//input', service_code)
                self.wait_and_click(f'//div[contains(., "{service_code}") and @role="option"]')
                self.browser.input_text_when_element_is_visible('//label[text()="Service Date"]/..//input[contains(@class, "hasDatepicker")]', self.cash_receipts.current_valid_date.strftime('%m/%d/%Y') + '\ue007')
                self.browser.input_text_when_element_is_visible('//label[text()="Amount"]/..//input', str(adjustment.amount))
                self.browser.click_element_when_visible('//button[text()="Apply Changes"]')

                reconcile_checked_buttons: list = self.browser.find_elements('//button[text()="Reconcile checked"]')
                for button in reconcile_checked_buttons:
                    if button.is_displayed():
                        self.wait_element(f'(//button[text()="Reconcile checked"])[{reconcile_checked_buttons.index(button) + 1}]')
                        button.click()
                        break
                self.browser.click_element_when_visible('//button[text()="Yes"]')
            else:
                common.log_message(f'{payment_id} already processed (L6)')
            return adjustment.amount
        else:
            common.log_message(f'Adjustments button not found. Payment ID {payment_id}')
        return 0.0

    def get_all_ids_from_era_list(self) -> list:
        payment_ids: list = []

        try_count: int = 0
        while True:
            current_len: int = len(payment_ids)
            elements: list = self.browser.find_elements('//a[@title="Copy ID"]')
            for elem in elements:
                current_id: str = elem.get_attribute('data-id')
                if current_id not in payment_ids:
                    payment_ids.append(current_id)
            self.browser.execute_javascript('scrollDiv = document.getElementsByClassName("ag-body-viewport"); scrollDiv[0].scrollBy(0, 250)')
            if current_len == len(payment_ids):
                try_count += 1
            if try_count == 3:
                break

        return payment_ids

    def find_payment_reference_and_apply_label(self, check_number: str):
        self.browser.go_to(f'{self.base_url}/#billingmanager/billing/?paymentReference={check_number}')
        self.wait_element(f'//em[contains(., "{check_number}")]')
        if self.is_no_results('Cannot find payment reference on CR'):
            common.log_message(f'Cannot find payment reference {check_number} on CentralReach')
            return
        self.browser.select_checkbox('//input[@data-bind="checked: listVm.allSelected"]')
        self.apply_label('No EOB')

    def adjustment_payments(self, eob_data: EOB, acnt_data: dict, check_number: str, payment_type) -> float:
        total_amount: float = 0.0
        # Adjustment Payments
        for adjustment in eob_data.adjustments:
            try:
                print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
                print(adjustment)
                if adjustment.identifier in acnt_data:
                    current_acnt: ACNT = acnt_data[adjustment.identifier]
                    # acnt_data.pop(adjustment.identifier)
                else:
                    current_acnt: ACNT = ACNT(adjustment.identifier)

                if 'WO' in adjustment.reason or 'FB' in adjustment.reason:
                    if 'FB' in adjustment.reason:
                        self.fb_modifications(self.cash_receipts.current_valid_date, eob_data.insurance_name)
                    else:
                        self.find_timesheet_by_claim_id(adjustment.identifier)
                        if self.is_no_results('No results'):
                            self.fb_modifications(self.cash_receipts.current_valid_date, eob_data.insurance_name)
                    if self.is_no_results('No results'):
                        common.log_message(f'No new timesheet was created')
                        continue

                    if self.check_payments_adjustment(check_number, payment_type, self.cash_receipts.current_valid_date, adjustment):
                        common.log_message(f'{adjustment.identifier} already processed')
                        total_amount += adjustment.amount
                        continue

                    notes: str = f'{adjustment.reason} {adjustment.numbers_for_notes} {"%.2f" % adjustment.amount} Takeback'
                    self.pre_bulk_apply_payments(payment_type, check_number, notes)
                    total_amount += self.bulk_apply_payments_adjustment(current_acnt, adjustment)
                    self.post_bulk_apply_payments(eob_data.insurance_name)

                    self.browser.select_checkbox('//input[@data-bind="checked: listVm.allSelected"]')
                    self.apply_label(adjustment.reason)
                elif 'L6' in adjustment.reason:
                    total_amount += self.interest_adjustment(check_number, eob_data.insurance_name, adjustment) * -1
            except Exception as ex:
                common.log_message(f'Processing error {adjustment.identifier}')
                common.log_message(str(ex))

                self.browser.capture_page_screenshot(
                    os.path.join(os.environ.get(
                        "ROBOT_ROOT", os.getcwd()),
                        'output',
                        f'Processing_error_{adjustment.identifier}_{datetime.datetime.now().strftime("%H_%M_%S")}.png'
                    )
                )
        return round(total_amount, 2)

    @staticmethod
    def get_sum(current_acnt: ACNT) -> float:
        amount: float = 0.0

        for service in current_acnt.services:
            amount += service.prov_pd
        return round(amount, 2)

    @staticmethod
    def get_notes(current_acnt: ACNT) -> str:
        # “ACNT #” + “(PR-#, CR#, OA#, PI#) AMT” (if applicable) in the notes
        notes: str = f'ACNT: {current_acnt.acnt_number} '
        for service in current_acnt.services:
            for reason_code in service.obligations:
                reason: str = str(reason_code.split('-')[0]).strip()
                if reason in ['PR', 'CR', 'OA', 'PI']:
                    notes += f'{reason_code} {service.obligations[reason_code]}'
        notes = notes.strip()
        return notes

    def validate_negative_amount(self) -> bool:
        if not self.headers_index:
            self.headers_index = self.find_header_index(
                ['client', 'date', 'payor', 'service/auth', 'agreed', 'pr amt.', 'paid', 'owed']
            )

        any_selected: bool = False
        rows: list = self.browser.find_elements('//tr[contains(@id, "billing-grid-row-")]')
        timesheets_data: dict = {}
        for row in rows:
            timesheet_id: str = row.get_attribute('id')
            timesheet_id = timesheet_id.split('-')[-1].strip()

            columns: list = row.find_elements_by_tag_name('td')
            owed_str: str = columns[self.headers_index['owed']].text
            timesheets_data[timesheet_id] = float(owed_str.replace(',', ''))

        self.browser.execute_javascript('window.scrollBy(-42000, -42000)')
        for timesheet_id in timesheets_data:
            if timesheets_data[timesheet_id] < 0:
                self.browser.scroll_element_into_view(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/input')
                self.browser.select_checkbox(f'//tr[@id="billing-grid-row-{timesheet_id}"]/td/input')
                any_selected = True
        return any_selected

    def non_adjustment_payments(self,  eob_data: EOB, acnt_data: dict, check_number: str, payment_type: str) -> float:
        total_amount: float = 0.0
        # Non-Adjustment Payments
        for acnt_number, current_acnt in acnt_data.items():
            try:
                print('-----------------------------------------------------------------------------')
                print(current_acnt)
                if not current_acnt.services:
                    common.log_message('ERROR: No service information found')
                    continue

                self.find_timesheet_by_claim_id(current_acnt.acnt_number)
                if self.is_no_results('No results found on the CentralReach'):
                    if eob_data.lockbox:
                        self.find_timesheet_by_invoice_id(current_acnt.acnt_number)
                    if self.is_no_results('No results found on the CentralReach'):
                        continue

                if self.check_payments(check_number, payment_type, self.cash_receipts.current_valid_date, current_acnt):
                    common.log_message(f'{current_acnt.acnt_number} already processed')
                    total_amount += self.get_sum(current_acnt)
                    continue
                notes: str = self.get_notes(current_acnt)
                self.pre_bulk_apply_payments(payment_type, check_number, notes)
                total_amount += self.bulk_apply_payments_non_adjustment(current_acnt)
                self.post_bulk_apply_payments(eob_data.insurance_name)

                self.browser.reload_page()
                if self.validate_negative_amount():
                    self.apply_label('CREDIT')
            except Exception as ex:
                common.log_message(f'Processing error {acnt_number}')
                common.log_message(str(ex))

                self.browser.capture_page_screenshot(
                    os.path.join(os.environ.get(
                        "ROBOT_ROOT", os.getcwd()),
                        'output',
                        f'Processing_error_{acnt_number}_{datetime.datetime.now().strftime("%H_%M_%S")}.png'
                    )
                )
        return round(total_amount, 2)

    def payments_processing(self):
        # init variables
        drive: GoogleDrive = GoogleDrive()
        pdf: PDF = PDF()
        specific_payer_types: list = [
            'Institutional: ASP'.upper(),
            'Institutional: SD'.upper(),
            'Regional Centers'.upper(),
            'Regional Centers'.upper(),
            'ESSC'.upper(),
            'the BHPN'.upper(),
        ]

        for row in self.cash_receipts.current_valid_dt.iter_dicts():
            check_number: str = str(row['Check Number']).strip().replace('.0', '')
            try:
                # Skip non bot rows
                if str(row['Payer Type']).strip().lower() == 'Patient Resp'.lower():
                    continue
                if 'ERA - NON'.lower() in str(row['Deposit Account']).strip().lower():
                    continue
                if row['Check Number'] is None or row['Applied'] is not None:
                    continue

                check_number: str = str(row['Check Number']).strip().replace('.0', '')
                if check_number.lower() == '#ERROR!'.lower():
                    print('_#ERROR! value')
                    continue
                check_number: str = re.sub(r'([-| ]\d{1,2}/\d{1,2}/\d{2,4})|(|=|"|\*)', '', check_number)
                deposit_account: str = str(row['Deposit Account']).strip()

                common.log_message('_________________________________________________________________')
                common.log_message(f'Start processing {check_number}')

                eob_data: EOB = EOB()
                acnt_data: dict = {}
                payment_type: str = ''
                if 'ACH'.lower() in deposit_account.lower():  # ACH or Electronic
                    payment_type: str = 'Electronic'
                elif 'Lockbox'.lower() in deposit_account.lower():
                    payment_type: str = 'Check'

                if str(row['Payer Type']).strip().upper() in specific_payer_types:
                    eob_data, acnt_data = self.lockbox_remit_other.read_lockbox_remit(check_number)
                elif 'ACH'.lower() in deposit_account.lower():
                    eob_data, acnt_data = self.waystar.get_payment_eob(check_number)
                elif 'Lockbox'.lower() in deposit_account.lower():
                    path_to_file: str = drive.download_file_by_part_of_name(check_number)
                    if path_to_file:
                        print('_File was found')
                        eob_data, acnt_data = pdf.parse_eob(path_to_file)
                    else:
                        print('_Cannot find PDF on GD')
                        eob_data, acnt_data = self.lockbox_remit_other.read_lockbox_remit(check_number)
                else:
                    continue

                if not eob_data.eft_number or not acnt_data:
                    if eob_data.eft_number:
                        common.log_message('Unable to obtain service codes from EOB')
                    else:
                        common.log_message(f'Cannot parse EOB data: {check_number}')
                    self.find_payment_reference_and_apply_label(check_number)
                    self.cash_receipts.write_to_current_month_cash_disbursement(row['index'], 'NR')
                    continue

                total_amount: float = .0
                total_amount += self.adjustment_payments(eob_data, acnt_data, check_number, payment_type)
                total_amount += self.non_adjustment_payments(eob_data, acnt_data, check_number, payment_type)
                self.browser.reload_page()
                # With a large amount of data is logging out
                self.waystar.login_to_site()
                self.cash_receipts.write_to_current_month_cash_disbursement(row['index'], 'x', round(total_amount, 2))
                drive.upload_file(self.cash_receipts.file_path)
            except Exception as ex:
                common.log_message(f'Processing error {check_number}')
                common.log_message(str(ex))

                self.browser.capture_page_screenshot(
                    os.path.join(os.environ.get(
                        "ROBOT_ROOT", os.getcwd()),
                        'output',
                        f'Processing_error_{check_number}_{datetime.datetime.now().strftime("%H_%M_%S")}.png'
                    )
                )

                self.browser.reload_page()
                self.cash_receipts.write_to_current_month_cash_disbursement(row['index'], 'NR')
                try:
                    exc_info = sys.exc_info()
                    traceback.print_exception(*exc_info)
                    del exc_info
                except Exception as ex:
                    print(str(ex))
                    pass

    def get_era_list_data(self, filter_name: str) -> dict:
        self.browser.go_to(f'{self.base_url}/#claims/eralist/')
        self.browser.reload_page()
        self.wait_element('//div[contains(@class, "ag-body-viewport")]')

        cr_requests: CentralReachRequests = CentralReachRequests(
            {
                'url': self.url,
                'login': self.login,
                'password': self.password,
            }
        )
        data: dict = {}
        if filter_name.lower() == 'Zero Pay'.lower():
            data: dict = cr_requests.get_zero_pay_filter(datetime.date.today().replace(day=1), datetime.date.today())
        elif filter_name.lower() == 'PR'.lower():
            data: dict = cr_requests.get_pr_filter(datetime.date.today().replace(day=1), datetime.date.today())
        elif filter_name.lower() == 'Denial'.lower():
            data: dict = cr_requests.get_denial_filter(datetime.date.today().replace(day=1), datetime.date.today())
        return data

    def zero_pay(self):
        common.log_message('Start zero pay processing')
        zero_pay: dict = self.get_era_list_data('Zero Pay')

        for payment_id, values in zero_pay.items():
            self.browser.reload_page()
            self.browser.go_to(f'https://members.centralreach.com/#claims/payments/?paymentId={payment_id}')
            self.wait_element(f'//a[text()="{payment_id}"]')
            self.reconcile_all(payment_id, True)

    def reconcile_all(self, payment_id: str, validate_pr: bool = True) -> None:
        self.wait_and_click('//button[text()="Reconcile All"]')
        self.wait_element('//div[@role="document"]/div[@class="modal-content"]')

        if self.browser.does_page_contain_element('//div[@role="document"]/div[@class="modal-content"]//p[text()="You have not selected any payments to reconcile."]'):
            self.wait_and_click('//button[text()="OK"]')
            return
        if self.browser.does_page_contain_element('//div[contains(@class, "alert") and contains(., "The following billing entries have already been reconciled")]'):
            self.wait_and_click('//button[text()="No"]')
            return

        common.log_message(f'Reconcile payment ID {payment_id}')
        pr_amount: str = str(self.browser.get_text('//label[text()="Patient Responsibility"]/../div')).strip()
        pr_activity_amount: str = str(self.browser.get_text('//label[text()="Patient Responsibility Activity"]/../div')).strip()
        if not validate_pr or (pr_amount == '$0.00' and pr_activity_amount == '$0.00'):
            self.wait_and_click('//button[text()="Yes"]')
            time.sleep(.5)
        else:
            common.log_message(f'Skip payment ID {payment_id} because PR amount is more than $0.00')

    def select_checkbox(self, checkboxes: list) -> None:
        for checkbox in checkboxes:
            if checkbox.get_attribute('id') == 'selected':
                self.browser.scroll_element_into_view(checkbox)
                self.browser.driver.execute_script("arguments[0].click();", checkbox)
                break

    def unselect_all_checkboxes(self) -> None:
        checkboxes: int = len(self.browser.find_elements('//input[@id="selected"]')) + 1
        for i in range(1, checkboxes):
            if self.browser.find_element(f'(//input[@id="selected"])[{i}]').is_selected():
                self.browser.scroll_element_into_view(f'(//input[@id="selected"])[{i}]')
                self.browser.execute_javascript(f'$("input#selected")[{i - 1}].click()')

    def select_patient_responsibility_rows(self, check_adjustment: bool = False) -> bool:
        rows: list = self.browser.find_elements('//div[contains(@class, "active")]//tr[@data-row-type]')
        current_b_row: int = 0
        current_calc_adj: float = .01
        any_selected: bool = False

        main_type: str = 'B'
        is_need_skip: bool = False
        for n in range(0, len(rows)):
            row_text: str = rows[n].text
            row_type: str = str(rows[n].get_attribute('data-row-type')).upper()

            if row_type != 'B' and is_need_skip:
                continue
            if 'Denials' in row_text or 'Orphaned' in row_text:
                is_need_skip = True
                continue
            is_need_skip = False

            if row_type == 'B' and 'Combined' in row_text:
                main_type: str = 'D'
            elif row_type == 'B':
                main_type: str = 'B'

            if row_type == main_type and check_adjustment:
                current_b_row: int = n

                columns: list = rows[n].find_elements_by_tag_name('td')
                if main_type == 'B':
                    current_column_type: str = 'B11'
                else:
                    current_column_type: str = 'D12'
                for col in columns:
                    if col.get_attribute('data-cell-type') == current_column_type:
                        current_calc_adj = float(str(col.text).strip().replace('$', '').replace(',', ''))
                        break
            if 'PR -' in row_text or 'PI -' in row_text or 'OR -' in row_text:
                if check_adjustment:
                    current_ins_adj: float = .0
                    for i in range(1, n - current_b_row):
                        columns: list = rows[n - i].find_elements_by_tag_name('td')
                        for col in columns:
                            if col.get_attribute('data-cell-type') == 'C15':
                                current_ins_adj += float(str(col.text).strip().replace('$', '').replace(',', ''))
                                break
                    if round(current_calc_adj, 2) == round(current_ins_adj, 2):
                        self.select_checkbox(rows[n].find_elements_by_tag_name('input'))
                        self.select_checkbox(rows[current_b_row].find_elements_by_tag_name('input'))
                        any_selected = True
                else:
                    self.select_checkbox(rows[n].find_elements_by_tag_name('input'))
                    self.select_checkbox(rows[current_b_row].find_elements_by_tag_name('input'))
                    any_selected = True
        return any_selected

    def change_label(self):
        label_add: str = 'PR'
        label_remove: str = 'CSELEC'

        self.wait_and_click('//button[text()="Bulk Actions "]')
        self.wait_and_click('//a[text()="Billing Entries"]')

        self.wait_element('//h4[text()="Apply Labels"]/../../div/div/div/ul/li/input')
        self.browser.input_text('//h4[text()="Apply Labels"]/../../div/div/div/ul/li/input', label_add)
        self.wait_element(f'//div[text()="{label_add}" and @role="option"]')
        if self.browser.does_page_contain_element("//div[@id='select2-drop']/ul[@class='select2-results']/li[@class='select2-no-results']"):
            self.browser.input_text('//h4[text()="Apply Labels"]/../../div/div/div/ul/li/input', label_add.lower())
            self.wait_element(f'//div[text()="{label_add}" and @role="option"]')
        self.browser.click_element_when_visible(f'//div[text()="{label_add}" and @role="option"]')

        self.wait_element('//h4[text()="Remove Labels"]/../../div/div/div/ul/li/input')
        self.browser.input_text('//h4[text()="Remove Labels"]/../../div/div/div/ul/li/input', label_remove)
        self.wait_element(f'//div[text()="{label_remove}" and @role="option"]')
        if self.browser.does_page_contain_element("//div[@id='select2-drop']/ul[@class='select2-results']/li[@class='select2-no-results']"):
            self.browser.input_text('//h4[text()="Remove Labels"]/../../div/div/div/ul/li/input', label_remove.lower())
            self.wait_element(f'//div[text()="{label_remove}" and @role="option"]')
        self.browser.click_element_when_visible(f'//div[text()="{label_remove}" and @role="option"]')

        self.browser.click_element_when_visible('//button[text()="Apply Label Changes"]')
        self.browser.wait_until_element_is_not_visible('//button[text()="Apply Label Changes"]')
        time.sleep(1)

    def pr_reconcile(self):
        common.log_message('Start PR reconcile processing')
        pr_data: dict = self.get_era_list_data('PR')

        for payment_id, values in pr_data.items():
            self.browser.reload_page()
            self.browser.go_to(f'https://members.centralreach.com/#claims/payments/?paymentId={payment_id}')
            self.wait_element(f'//a[text()="{payment_id}"]')

            common.log_message(f'PR reconcile payment ID {payment_id}')
            # Add label "PR" and remove label "CSELEC"
            self.unselect_all_checkboxes()
            if not self.select_patient_responsibility_rows():
                common.log_message(f'None selected')
                continue

            self.change_label()

            # Reconcile all if calc adj == ins adj
            self.unselect_all_checkboxes()
            if not self.select_patient_responsibility_rows(True):
                common.log_message(f'Payment ID {payment_id} was skipped. Calc Adj is not equal to Ins Adj')
                continue
            self.reconcile_all(payment_id, False)

    def denial(self):
        common.log_message('Start denial processing')
        denial_data: dict = self.get_era_list_data('Denial')

        for key, value in denial_data.items():
            eob_data, acnt_data = self.waystar.get_payment_eob(value['CheckNumber'])

            if not eob_data.denial:
                common.log_message(f'Unable to find denial code for check number {value["CheckNumber"]}')
                continue

            common.log_message(f'Start processing check number {value["CheckNumber"]}')
            for acnt_number, current_acnt in acnt_data.items():
                self.browser.reload_page()
                # ACNT# + Denial Code
                notes: str = f'ACNT: {current_acnt.acnt_number} {eob_data.denial_code}'
                self.find_timesheet_by_claim_id(current_acnt.acnt_number)
                if self.is_no_results('No results'):
                    continue
                if self.check_payments(value['CheckNumber'], 'Electronic', eob_data.date, current_acnt):
                    common.log_message(f'{current_acnt.acnt_number} already processed')
                    continue

                self.pre_bulk_apply_payments('Electronic', value['CheckNumber'], notes)
                self.post_bulk_apply_payments(eob_data.insurance_name)

    def reconcile_zero_payments_and_denials(self):
        self.zero_pay()

        self.pr_reconcile()

        self.denial()
