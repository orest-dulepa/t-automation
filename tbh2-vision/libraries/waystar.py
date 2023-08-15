from RPA.Browser.Selenium import Selenium
import fitz
from libraries import common
from urllib.parse import urlparse
import datetime
import time
import os
import shutil
import re
import traceback
from libraries.models.timesheet import Timesheet
from libraries.models.insurance import Insurance
from libraries.models.client import Client


class WayStar:

    def __init__(self, credentials: dict):
        self.credentials: dict = credentials
        self.browser: Selenium = Selenium()
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.base_url: str = self.get_base_url()
        self.path_to_temp: str = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'waystar')
        self.login_to_site()
        self.start_url: str = self.browser.get_location()
        self.npi: dict = {}
        self.crosswalk_guide: dict = {}

    def get_base_url(self):
        parsed_uri = urlparse(self.url)
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

    def login_to_site(self):
        self.browser.close_browser()
        self.browser.timeout = 45
        self.is_site_available = False
        count = 1

        if os.path.exists(self.path_to_temp):
            shutil.rmtree(self.path_to_temp)
        os.mkdir(self.path_to_temp)
        preferences = {
            'download.default_directory': self.path_to_temp,
            'plugins.always_open_pdf_externally': True,
            'download.directory_upgrade': True,
            'download.prompt_for_download': False
        }

        while count < 2 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.url, preferences=preferences)
                self.browser.set_window_size(1920, 1080)
                self.browser.maximize_browser_window()
                common.wait_element(self.browser, '//input[@type="password"]', is_need_screen=False)
                self.browser.input_text_when_element_is_visible('//input[@type="text"]', self.login)
                self.browser.input_text_when_element_is_visible('//input[@type="password"]', self.password)
                self.browser.click_button_when_visible('//input[@id="loginButton"]')

                if self.browser.does_page_contain_element('//h1[text()="Login failed"]'):
                    elem = self.browser.find_element('//h1[text()="Login failed"]')
                    if elem.is_displayed():
                        raise Exception('Logging into WayStar failed')

                common.wait_element_and_refresh(self.browser, '//h1[contains(., "Professional Claims")]', 5, is_need_screen=False)
                if self.browser.does_page_contain_element('//h2[text()="Additional Authentication Required"]'):
                    question: str = str(self.browser.get_text('//strong')).strip()
                    if question in self.credentials:
                        self.browser.input_text_when_element_is_visible('//input[@id="verifyAnswer"]', self.credentials[question])
                        self.browser.click_element_when_visible('//input[@id="VerifyButton"]')
                        common.wait_element_and_refresh(self.browser, '//h1[contains(., "Professional Claims")]', 5, is_need_screen=False)

                while self.browser.does_page_contain_element('//button[contains(@onclick, "alert")]'):
                    self.browser.click_element_when_visible('//button[contains(@onclick, "alert")]')
                    common.wait_element_and_refresh(self.browser, '//h1[contains(., "Professional Claims")]', 3, is_need_screen=False)

                self.is_site_available = self.browser.does_page_contain_element('//h1[contains(., "Professional Claims")]')
            except Exception as ex:
                common.log_message("Logging into WayStar. Attempt #{} failed".format(count), 'ERROR')
                common.log_message(str(ex))
                self.browser.capture_page_screenshot(
                    os.path.join(
                        os.environ.get("ROBOT_ROOT", os.getcwd()),
                        'output',
                        f'WayStar_login_failed_{count}.png'
                    )
                )
                self.browser.close_browser()
            finally:
                count += 1
                if not self.is_site_available:
                    self.browser.capture_page_screenshot(
                        os.path.join(
                            os.environ.get("ROBOT_ROOT", os.getcwd()),
                            'output',
                            f'WayStar_login_failed.png'
                        )
                    )

    def does_claim_rejected(self, claim_id: str) -> bool:
        self.close_not_used_window()
        tab = self.browser.get_window_handles()
        self.browser.switch_window(tab[0])
        self.check_if_need_login_again()

        self.browser.go_to(self.start_url)
        time.sleep(5)

        common.wait_element(self.browser, '//select[@id="SearchCriteria_Status"]')
        self.browser.select_from_list_by_value('//select[@id="SearchCriteria_Status"]', '-1')
        self.browser.input_text_when_element_is_visible('//input[@id="SearchCriteria_PatNumber"]', claim_id)

        self.browser.click_element_when_visible('//input[@id="ClaimListingSearchButtonBottom"]')
        common.click_and_wait(self.browser, '//input[@id="ClaimListingSearchButtonBottom"]', f'//td[contains(@class, "patientNumberCell") and contains(.,"{ claim_id }")]', timeout=60 * 3)
        if self.browser.does_page_contain_element(f'//td[contains(@class, "patientNumberCell") and contains(.,"{ claim_id }")]'):
            timer = datetime.datetime.now() + datetime.timedelta(0, 60 * 7)
            status: str = ''

            while timer > datetime.datetime.now():
                try:
                    status = 'processing'
                    if self.browser.does_page_contain_element('//a[contains(@class, "claimStatusLink")]'):
                        status: str = self.browser.get_text('//a[contains(@class, "claimStatusLink")]')
                    if 'processing' in status.lower() or 'in process' in status.lower() or 'In Progress'.lower() in status.lower():
                        time.sleep(10)
                        self.browser.select_from_list_by_value('//select[@id="SearchCriteria_Status"]', '-1')
                        self.browser.input_text_when_element_is_visible('//input[@id="SearchCriteria_PatNumber"]', claim_id)
                        self.browser.click_element_when_visible('//input[@id="ClaimListingSearchButtonBottom"]')
                        self.browser.wait_until_element_is_not_visible('//span[text()="Please run a search."]', datetime.timedelta(seconds=60 * 2))
                        common.wait_element(self.browser, f'//td[contains(@class, "patientNumberCell") and contains(.,"{claim_id}")]', timeout=10, is_need_screen=False)
                    else:
                        break
                except:
                    time.sleep(10)
            try:
                status: str = self.browser.get_text('//a[contains(@class, "claimStatusLink")]')
            except Exception as error:
                print('dcr2(): ' + str(error))
                self.browser.capture_page_screenshot(
                    os.path.join(
                        os.environ.get("ROBOT_ROOT", os.getcwd()),
                        'output',
                        'dcr2_{}.png'.format(datetime.datetime.now().strftime('%H_%M_%S')))
                )
            if 'rejected' not in status.lower():
                return False
        else:
            print('dcr3(): Element not available')
        return True

    def edit_payor_info(self, insurance: Insurance):
        self.browser.click_element_when_visible('//input[@id="ins_ChangePayerButton"]')
        common.wait_element(self.browser, '//input[@id="ins_SaveButton"]')

        current_insurance: str = self.browser.get_value('//input[@name="ins$name"]')
        if insurance.payer_name.upper() not in current_insurance.upper():
            if insurance.payer_name:
                self.browser.input_text_when_element_is_visible('//input[@name="ins$name"]', insurance.payer_name)
        if insurance.payer_id:
            self.browser.input_text_when_element_is_visible('//input[@name="ins$payerid"]', insurance.payer_id)
        if insurance.address:
            self.browser.input_text_when_element_is_visible('//input[@name="ins$payeradd1"]', insurance.address)

        self.browser.click_element_when_visible('//input[@id="ins_SaveButton"]')
        common.wait_element(self.browser, '//input[@name="ins$ConfirmOkButton"]', 5, False)
        if self.browser.does_page_contain_element('//input[@name="ins$ConfirmOkButton"]'):
            if self.browser.find_element('//input[@name="ins$ConfirmOkButton"]').is_displayed():
                self.browser.click_element_when_visible('//input[@name="ins$ConfirmOkButton"]')
        self.browser.wait_until_element_is_not_visible('//input[@id="ins_SaveButton"]')

    def populate_subscriber_info(self, insurance: Insurance):
        if 'CO Medicaid'.lower() in insurance.payer_name.lower():
            self.browser.select_from_list_by_value('//select[@name="ins$FV3$relation"]', '18')
        else:
            self.browser.select_from_list_by_value('//select[@name="ins$FV3$relation"]', '19')
        self.browser.select_from_list_by_value('//select[@id="ins_FV3_releaseinfo"]', 'Y')
        self.browser.select_from_list_by_value('//select[@id="ins_FV3_assignbenefits"]', 'Y')

        if insurance.subscriber_last_name:
            self.browser.input_text_when_element_is_visible('//input[@name="ins$FV3$lname"]', insurance.subscriber_last_name)
        if insurance.subscriber_first_name:
            self.browser.input_text_when_element_is_visible('//input[@name="ins$FV3$fname"]', insurance.subscriber_first_name)
        if insurance.subscriber_middle_name:
            self.browser.input_text_when_element_is_visible('//input[@name="ins$FV3$mname"]', insurance.subscriber_middle_name)
        if insurance.subscriber_address:
            self.browser.input_text_when_element_is_visible('//input[@name="ins$FV3$add1"]', insurance.subscriber_address)
        if insurance.subscriber_id:
            self.browser.input_text_when_element_is_visible('//input[@name="ins$FV3$membernum"]', insurance.subscriber_id)
        if insurance.subscriber_dob:
            self.browser.input_text_when_element_is_visible('//input[@name="ins$FV3$birthdate"]', insurance.subscriber_dob)
        if insurance.subscriber_gender:
            self.browser.select_from_list_by_value('//select[@id="ins_FV3_sex"]', insurance.subscriber_gender)

    def populate_provider_info(self, client: Client, insurance_name: str, location: str, provider_info: dict) -> None:
        common.wait_element(self.browser, '//a[text()="Provider"]')
        self.browser.click_element_when_visible('//a[text()="Provider"]')

        common.wait_element(self.browser, '//span[text()="Facility"]')
        if 'CO Medicaid'.lower() in insurance_name.lower():
            self.browser.click_element_when_visible('//span[text()="Facility"]')
            common.wait_element(self.browser, '//input[@name="prt$tc$facTP$fac$FV$name"]')
            self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$facTP$fac$FV$name"]', '')
            self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$facTP$fac$FV$add1"]', '')
            self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$facTP$fac$FV$add2"]', '')
            self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$facTP$fac$FV$city"]', '')
            self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$facTP$fac$FV$state"]', '')
            self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$facTP$fac$FV$zip"]', '')
            self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$facTP$fac$FV$country"]', '')
            self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$facTP$fac$FV$countrysub"]', '')
            self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$facTP$fac$FV$npi"]', '')
            self.browser.click_element_when_visible('//span[text()="Billing"]')
            common.wait_element(self.browser, '//input[@name="prt$tc$bilTP$bil$FV$npi"]')
            npi: str = self.browser.get_value('//input[@name="prt$tc$bilTP$bil$FV$npi"]')
            if 'CO Medicaid' in insurance_name and '1588967236' == npi.strip():
                if location.lower() in self.npi:
                    new_npi: str = self.npi[location.lower()]['npi']
                    self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$bilTP$bil$FV$npi"]', new_npi)
                else:
                    common.log_message("Can't find the NPI")

        common.wait_element(self.browser, '//span[text()="Rendering"]')
        self.browser.click_element_when_visible('//span[text()="Rendering"]')

        common.wait_element(self.browser, '//input[@name="prt$tc$renTP$ren$FV$lname"]')
        if provider_info:
            self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$renTP$ren$FV$lname"]', provider_info['last_name'])
            self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$renTP$ren$FV$fname"]', provider_info['first_name'])
            self.browser.input_text_when_element_is_visible('//input[@name="prt$tc$renTP$ren$FV$npi"]', provider_info['npi_number'])
        else:
            last_name: str = self.browser.get_value('//input[@name="prt$tc$renTP$ren$FV$lname"]')
            first_name: str = self.browser.get_value('//input[@name="prt$tc$renTP$ren$FV$fname"]')
            npi: str = self.browser.get_value('//input[@name="prt$tc$renTP$ren$FV$npi"]')
            if not last_name or not first_name or not npi:
                print(f'Last name {last_name}. First name {first_name}. NPI {npi}')

    def update_claim_info(self, eob_data: dict):
        common.wait_element(self.browser, '//a[text()="Claim"]')
        self.browser.click_element_when_visible('//a[text()="Claim"]')

        common.wait_element(self.browser, '//div[@id="clt_UP"]')
        common.wait_element(self.browser, '//span[text()="COB"]')
        self.browser.click_element_when_visible('//span[text()="COB"]')

        common.wait_element(self.browser, '//table[@id="clt_tc_cobTP_cob_FV"]')

        claim_paid_date: str = ''
        payer_paid: float = .0
        amt_owed: float = .0
        for service, list_of_data in eob_data['services'].items():
            if not claim_paid_date:
                claim_paid_date = eob_data['check date']
            for item in list_of_data:
                payer_paid += float(str(item['paid_amount']).replace(',', ''))
                amt_owed += float(str(item['patient_liability']).replace(',', ''))

        self.browser.input_text_when_element_is_visible('//td/input[contains(@name, "claimpaiddate")]', claim_paid_date)
        self.browser.input_text_when_element_is_visible('//td/input[contains(@name, "payerpaid")]', str(payer_paid))
        self.browser.input_text_when_element_is_visible('//td/input[contains(@name, "amtowed")]', str(amt_owed))

    @staticmethod
    def get_service_info(eob_data: dict, service_code: str, amount: str) -> dict:
        if service_code not in eob_data['services']:
            return {}
        for item in eob_data['services'][service_code]:
            if item['billed'] == amount:
                return item
        return {}

    def update_service_line_info(self, eob_data: dict):
        common.wait_element(self.browser, '//a[text()="Service Line"]')
        self.browser.click_element_when_visible('//a[text()="Service Line"]')
        common.wait_element(self.browser, '//div[@id="ServiceLinesDiv"]')

        self.browser.click_element_when_visible('//span[text()="COB"]')
        common.wait_element(self.browser, '//td/input[contains(@name, "claimpaiddate")]')

        service_lines: list = self.browser.find_elements('//table[@id="slv_FV_GV"]/tbody/tr')
        for row in service_lines[1:]:
            index: int = service_lines.index(row)
            self.browser.click_element_when_visible(f'//table[@id="slv_FV_GV"]/tbody/tr/td/span[text()="{index}"]')
            common.wait_element(self.browser, f'//div[@id="slv_UP2"]/div/span[text()="{index}"]')
            time.sleep(10)

            service_from_web: str = str(self.browser.get_value(f'(//td/input[contains(@name, "proccode")])[{index}]')).upper()
            amount_from_web: str = self.browser.get_value(f'(//td/input[contains(@name, "chg")])[{index}]')
            amount_from_web = amount_from_web.replace(',', '')
            try:
                if service_from_web not in eob_data['services']:
                    if service_from_web in self.crosswalk_guide and len(self.crosswalk_guide[service_from_web]) == 1:
                        service_from_web = self.crosswalk_guide[service_from_web][0]

                info: dict = self.get_service_info(eob_data, service_from_web, amount_from_web)
                unit: str = self.browser.get_value(f'(//td/input[contains(@name, "qty")])[{index}]')

                self.browser.input_text_when_element_is_visible('//td/input[contains(@name, "claimpaiddate")]', info['check date'])
                self.browser.input_text_when_element_is_visible('//td[contains(., "Paid Units of Service")]/../td/input[contains(@name, "qty")]', unit)
                self.browser.input_text_when_element_is_visible('//td/input[contains(@name, "payerpaid")]', info['paid_amount'])

                self.browser.input_text_when_element_is_visible('//td/input[contains(@name, "amtowed")]', info['patient_liability'])
                self.browser.select_from_list_by_value('//td/select[contains(@name, "proctype")]', 'HC')
                self.browser.input_text_when_element_is_visible('//td/select[contains(@name, "proctype")]/following-sibling::input[contains(@name, "proccode")]', info['service code'])

                # Populate Adjustment Groups
                self.browser.select_from_list_by_value('(//td/select[contains(@name, "group")])[1]', 'CO')
                self.browser.input_text_when_element_is_visible('(//td[contains(., "Amount")]/../td/input[contains(@name, "amt")])[1]', info['obligation_amount'])
                self.browser.input_text_when_element_is_visible('(//td/input[contains(@name, "reason")])[1]', info['obligation_code'])

                if not self.browser.does_page_contain_element('(//td/select[contains(@name, "group")])[2]'):
                    self.browser.click_element_when_visible('//a[text()="Add an Adjustment Group"]')
                common.wait_element(self.browser, '(//td/select[contains(@name, "group")])[2]')
                self.browser.select_from_list_by_value('(//td/select[contains(@name, "group")])[2]', 'PR')
                self.browser.input_text_when_element_is_visible('(//td[contains(., "Amount")]/../td/input[contains(@name, "amt")])[2]', info['patient_liability'])
                self.browser.input_text_when_element_is_visible('(//td/input[contains(@name, "reason")])[2]', info['patient_liability_code'])
            except Exception as ex:
                print(f'update_service_line_info(): {service_from_web}. {str(ex)}')
                traceback.print_exc()

    @staticmethod
    def get_index(line_from_pdf: str, search_word: str) -> int:
        temp_array: list = line_from_pdf.split('\n')
        for item in temp_array:
            if search_word in item:
                return temp_array.index(item)
        return -1

    def read_remit_file(self) -> str:
        path_to_pdf: str = common.get_downloaded_file_path(self.path_to_temp, '.pdf', 'Cannot download Remit file')

        text: str = ""
        with fitz.Document(path_to_pdf) as doc:
            for page in doc:
                text += page.getText()
        os.remove(path_to_pdf)

        return text

    def parse_remit_file(self, eob_data: dict, date_of_service: datetime):
        text: str = self.read_remit_file()
        text_array: list = text.split('\n')

        date_of_service_short_str: str = date_of_service.strftime('%m%d%y')
        date_of_service_long_str: str = date_of_service.strftime('%m%d%Y')

        temp_check_date: str = ''
        patient_liability_code: str = ''
        for i in range(len(text_array)):
            line: str = str(text_array[i]).strip()
            if 'CHECK DATE:' in line:
                temp_check_date: str = str(text_array[i + 1]).strip()
                eob_data['check date'] = temp_check_date
            if date_of_service_short_str in line or date_of_service_long_str in line:
                new_position: int = i + 1
                while len(str(text_array[new_position]).strip()) != 5:
                    new_position += 1

                service = str(text_array[new_position]).strip().upper()
                if service not in eob_data['services']:
                    eob_data['services'][service] = []

                check_mod = re.search(r'\d+\.\d{2}', str(text_array[new_position + 1]).strip())
                modifier: str = ''

                if check_mod is None:
                    new_position += 1
                    modifier: str = str(text_array[new_position]).strip()

                billed: str = ''
                prov_pd: str = ''
                patient_liability: str = ''
                obligation_amount: str = ''
                obligation_code: str = ''
                count: int = 0

                while True:
                    new_position += 1
                    check_amount = re.search(r'\d+\.\d{2}', str(text_array[new_position]).strip())
                    if check_amount is None:
                        obligation_code = str(text_array[new_position]).strip().split('-')[-1].strip()
                        continue
                    count += 1
                    if count == 1:
                        billed = str(text_array[new_position]).strip()

                        check_billed: list = billed.split()
                        if len(check_billed) == 2:
                            billed = check_billed[0]
                            count += 1
                        elif len(check_billed) == 3:
                            billed = check_billed[0]
                            count += 2
                    elif count == 3 and 'Deductible Amount' in text:
                        patient_liability = str(text_array[new_position]).strip()
                    elif count == 4 and not patient_liability:
                        patient_liability = str(text_array[new_position]).strip()
                    elif count == 5:
                        obligation_amount = str(text_array[new_position]).strip()
                    elif count == 6:
                        prov_pd = str(text_array[new_position]).strip()

                        check_prov_pd: list = prov_pd.split()
                        if len(check_prov_pd) == 2:
                            prov_pd = check_prov_pd[0]
                        break
                eob_data['services'][service].append({
                    'billed': billed,
                    'modifier': modifier,
                    'paid_amount': prov_pd,
                    'patient_liability': patient_liability,
                    'patient_liability_code': '',
                    'obligation_amount': obligation_amount,
                    'obligation_code': obligation_code,
                    'service code': service,
                    'check date': temp_check_date,
                })

            if 'Patient Responsibility' in line:
                patient_liability_code: str = str(text_array[i + 1]).strip().split()[0].strip()
                if re.findall(r'(\d+)', patient_liability_code):
                    patient_liability_code = re.findall(r'(\d+)', patient_liability_code)[0]

        is_new_patient_liability_added: bool = False
        new_patient_liability: str = ''
        if 'PR-' + patient_liability_code in text_array:
            new_patient_liability = text_array[text_array.index('PR-' + patient_liability_code) + 1]

        for service in eob_data['services']:
            for service_item in eob_data['services'][service]:
                service_item['patient_liability_code'] = patient_liability_code
                if new_patient_liability and not is_new_patient_liability_added:
                    service_item['patient_liability'] = new_patient_liability
                    is_new_patient_liability_added = True

    def download_and_parse_remit_file(self, date_of_service: datetime) -> dict:
        eob_data: dict = {
            'services': {}
        }

        try:
            count_of_files = len(self.browser.find_elements('//span[@title="Has Remit"]'))
        except:
            time.sleep(2)
            count_of_files = len(self.browser.find_elements('//span[@title="Has Remit"]'))

        for n in range(1, count_of_files + 1):
            try:
                tab = self.browser.get_window_handles()
                self.browser.switch_window(tab[0])

                self.browser.click_element_when_visible(f'(//span[@title="Has Remit"])[{n}]')
                try:
                    tab = self.browser.get_window_handles()
                    self.browser.switch_window(tab[-1])

                    path_to_pdf: str = common.get_downloaded_file_path(self.path_to_temp, '.pdf')

                    if path_to_pdf:
                        self.parse_remit_file(eob_data, date_of_service)
                    elif self.browser.does_page_contain_element('//a[text()="EOB"]'):
                        count: int = len(self.browser.find_elements('//a[text()="EOB"]'))
                        for i in range(1, count + 1):
                            self.browser.click_element_when_visible(f'(//a[text()="EOB"])[{i}]')
                            self.parse_remit_file(eob_data, date_of_service)
                except Exception as download_error:
                    if 'Cannot download Remit file' in str(download_error):
                        raise Exception
                    common.log_message(f'OEB download: {str(download_error)}')
                    self.parse_remit_file(eob_data, date_of_service)
                finally:
                    tab = self.browser.get_window_handles()
                    self.browser.switch_window(tab[-1])
                    self.browser.close_window()
                    self.browser.switch_window(tab[0])
            except Exception as error:
                common.log_message(f'OEB: {str(error)}')
                traceback.print_exc()
        return eob_data

    def check_if_need_login_again(self):
        if self.browser.does_page_contain_element('//input[@type="text" and @name="loginName"]') \
                or self.browser.does_page_contain_element('//input[@type="password"]'):
            self.login_to_site()

    def select_date(self, date_of_service: datetime):
        common.wait_element(self.browser, '//div[@id="ui-datepicker-div"]')
        self.browser.select_from_list_by_value('//div[@id="ui-datepicker-div"]//select[@data-handler="selectMonth"]', str(date_of_service.month - 1))
        self.browser.select_from_list_by_value('//div[@id="ui-datepicker-div"]//select[@data-handler="selectYear"]', str(date_of_service.year))
        self.browser.click_element_when_visible(f'//div[@id="ui-datepicker-div"]//a[text()="{date_of_service.day}"]')
        self.browser.wait_until_element_is_not_visible('//div[@id="ui-datepicker-div"]')

    def search_by_client(self, client_name: str, date_of_service: datetime, claim_id: str = ''):
        tab = self.browser.get_window_handles()
        self.browser.switch_window(tab[0])
        self.check_if_need_login_again()

        self.browser.go_to(self.start_url)

        common.wait_element(self.browser, '//select[@id="SearchCriteria_Status"]')
        self.browser.select_from_list_by_value('//select[@id="SearchCriteria_Status"]', '-1')
        self.browser.input_text_when_element_is_visible('//input[@id="SearchCriteria_PatientNames"]', client_name)

        self.browser.select_from_list_by_value('//select[@id="SearchCriteria_ServiceDate"]', 'Custom')
        common.wait_element(self.browser, '//input[@id="serviceDateFromDateBox"]')

        self.browser.click_element_when_visible('//input[@id="serviceDateFromDateBox"]')
        self.select_date(date_of_service)

        self.browser.click_element_when_visible('//input[@id="serviceDateToDateBox"]')
        self.select_date(date_of_service)

        self.browser.select_from_list_by_value('//select[@id="SearchCriteria_TransDate"]', '2 years')

        self.browser.click_element_when_visible('//input[@id="ClaimListingSearchButtonBottom"]')
        common.click_and_wait(self.browser, '//input[@id="ClaimListingSearchButtonBottom"]', f'//td[contains(@class, "patientNumberCell") and contains(.,"{ claim_id }")]')
        self.browser.wait_until_element_is_not_visible('//div[@id="progressBackgroundFilter"]')

    def close_not_used_window(self):
        tabs = self.browser.get_window_handles()
        for i in range(len(tabs) - 1, 0, -1):
            try:
                self.browser.switch_window(tabs[i])
                self.browser.close_window()
            except:
                pass

        tabs = self.browser.get_window_handles()
        self.browser.switch_window(tabs[0])

    def get_eob_data(self, client_name: str, date_of_service: datetime, claim_id: str = '') -> dict:
        self.close_not_used_window()

        client_name_new: str = client_name
        if len(client_name.split()) > 2:
            client_name_new: str = client_name.split()[0] + ' ' + client_name.split()[-1]
        self.search_by_client(client_name_new, date_of_service, claim_id)
        if not self.browser.does_page_contain_element('//span[@title="Has Remit"]'):
            common.log_message('ERROR: EOB button does not exist', 'ERROR')
            return {'services': {}}

        eob_data: dict = self.download_and_parse_remit_file(date_of_service)
        self.close_not_used_window()

        return eob_data

    def update_insurance_info(self, timesheet: Timesheet):
        common.wait_element(self.browser, '//a[text()="Insurance"]')
        self.browser.click_element_when_visible('//a[text()="Insurance"]')

        common.wait_element(self.browser, '//span[contains(@id, "seqLabel")]/../..')
        rows_count: int = len(self.browser.find_elements('//span[contains(@id, "seqLabel")]/../..'))
        for i in range(1, rows_count + 1):
            self.browser.click_element_when_visible(f'(//span[contains(@id, "seqLabel")]/../..)[{i}]//input')
            self.browser.click_element_when_visible('//a[@id="ins_Reorder"]')
            self.browser.wait_until_element_is_not_visible(f'(//span[contains(@id, "seqLabel")]/../..)[{i}]//a[text()="Delete"]', datetime.timedelta(seconds=60 * 2))

            current_row: str = self.browser.get_text(f'(//span[contains(@id, "seqLabel")]/../..)[{i}]')
            if 'Primary'.lower() in current_row.lower():
                address: str = self.browser.get_text('//span[@id="ins_FV1_add1Label"]')
                if address.lower() != timesheet.primary_payor.address.lower():
                    self.edit_payor_info(timesheet.primary_payor)
                self.populate_subscriber_info(timesheet.primary_payor)
            if 'Secondary'.lower() in current_row.lower():
                self.edit_payor_info(timesheet.secondary_payor)
                self.populate_subscriber_info(timesheet.secondary_payor)
                break

    def review_rendering(self) -> dict:
        provider_info: dict = {}
        common.wait_element(self.browser, '//a[text()="Service Line"]')
        self.browser.click_element_when_visible('//a[text()="Service Line"]')

        common.wait_element(self.browser, '//div[@id="ServiceLinesDiv"]')
        self.browser.click_element_when_visible('//span[text()="Provider"]')
        common.wait_element(self.browser, '//label[text()="Individual (Last, First, Middle, Suffix)"]')

        if not self.browser.does_page_contain_element('//input[@checked="checked"]/../label[text()="Individual (Last, First, Middle, Suffix)"]'):
            common.log_message('WARNING: The provider is not selected as Individual')
            return provider_info

        provider_info['last_name'] = self.browser.get_value('//td/input[contains(@name, "lname")]')
        provider_info['first_name'] = self.browser.get_value('//td/input[contains(@name, "fname")]')
        provider_info['npi_number'] = self.browser.get_value('//td/input[contains(@name, "npi")]')

        return provider_info

    def edit_waystar_claim(self, claim_id: str, timesheet: Timesheet, timesheets: list, eob_data: dict = None) -> bool:
        try:
            self.close_not_used_window()

            if not eob_data:
                eob_data: dict = self.get_eob_data(timesheet.client.client_name, timesheet.date_of_service, timesheet.claim_id)
            if not eob_data['services']:
                common.log_message('ERROR: Cannot parse PDF')
                return False
            rejected: bool = self.does_claim_rejected(claim_id)

            try:
                self.browser.click_element_when_visible(f'//td[contains(., "{claim_id}")]')
            except Exception as ex:
                print(f'_click claim_id {str(ex)}')
                self.browser.click_element_when_visible(f'//td[contains(@class, "patientNumberCell")]')

            common.wait_element(self.browser, '//a[text()="Edit"]')
            self.browser.click_element_when_visible('//a[text()="Edit"]')

            tabs = self.browser.get_window_handles()
            if len(tabs) == 1:
                common.wait_element(self.browser, '//span[text()="OK"]/..', timeout=15)
                if self.browser.does_page_contain_element('//span[text()="OK"]/..'):
                    self.browser.click_element_when_visible('//span[text()="OK"]/..')
            tabs = self.browser.get_window_handles()
            self.browser.switch_window(tabs[1])
            self.browser.set_window_size(1920, 1080)

            if rejected:
                self.update_insurance_info(timesheet)
                provider_info: dict = {}
                if 'Tricare'.lower() in timesheet.secondary_payor.payer_name.lower():
                    provider_info: dict = self.review_rendering()
                self.populate_provider_info(timesheet.client, timesheet.current_payor, timesheet.client.location_city, provider_info)

            self.update_service_line_info(eob_data)
            self.update_claim_info(eob_data)

            self.browser.click_element_when_visible('//input[@name="ResubmitButton"]')
            time.sleep(3)
            # self.browser.close_window()

            return True
        except Exception as ex:
            common.log_message('edit_waystar_claim(): ' + str(ex), 'ERROR')
            self.browser.capture_page_screenshot(os.path.join(
                os.environ.get("ROBOT_ROOT", os.getcwd()),
                'output',
                f'Something_went_wrong_WS_{claim_id}.png')
            )
            traceback.print_exc()
        return False


if __name__ == '__main__':
    pass
