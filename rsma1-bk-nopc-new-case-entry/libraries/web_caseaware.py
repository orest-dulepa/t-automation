import decimal
import glob
import re
import traceback
from datetime import datetime, timedelta
from RPA.Browser.Selenium import Selenium
from selenium.webdriver.common.keys import Keys
from libraries import common as com
from libraries import word
from PyPDF2 import PdfFileMerger
import time
import os
from urllib.parse import urlparse
from libraries.send_mail import MailMessage
from RPA.Outlook.Application import Application


class CaseAware:
    REF_SITE_MAPPING = {
        'MI': '1',
        'WI': '10',
        'CO': '18',
        'IL': '4',
        'MN': '3',
        'WY': '19'
    }

    LOAN_TYPE_MAPPING = {
        'Conventional Uninsured': '3',
        'FHA Residential': '6',
        'USDA': '19',
        'VA Residential': '10'
    }

    ATTORNEY_VALUE_MAPPING = {
        'Toebben, Scott': '235',
        'Guyer, Brian': '339',
        'Major, James': '253',
        'Less, Jennifer': '180',
        'Thieme, Mary': '345',
    }

    # last used atty
    ATTORNEY_STATE_MAPPING = {
        'IL': {
            'last_used_id': 0,
            'user_list': ['Guyer, Brian', 'Major, James']
        },
        'MI': {
            'last_used_id': 0,
            'user_list': ['Thieme, Mary']  # 'Less, Jennifer',
        },
        'WI': {
            'last_used_id': 0,
            'user_list': ['Guyer, Brian']
        },
        'MN': {
            'last_used_id': 0,
            'user_list': ['Major, James']
        },
        'CO': {
            'last_used_id': 0,
            'user_list': ['Toebben, Scott']
        },
        'WY': {
            'last_used_id': 0,
            'user_list': ['Toebben, Scott']
        }
    }

    UPLOAD_DOC_MAPPING = {
        'Docket': '55',
        'Bankruptcy Documents': '28',
        'POC': '71',
        'Escrow Breakdown': '87',
        'NOPC': '272',
        'ARM Change': '272',
        'default': '191',
        'bk_Certificate of Service': '288'
    }

    def __init__(self, credentials: dict, mail_creds: dict, is_test_run: bool = False):
        self.test_run: bool = is_test_run
        self.is_failed: bool = False
        self.error_message: str = ''
        self.browser: Selenium = Selenium()
        self.credentials: dict = credentials
        self.bot_creds = mail_creds
        self.base_url: str = self.get_base_url()
        self.is_site_available: bool = False
        self.file_found: bool = False
        root_path = os.environ.get("ROBOT_ROOT", os.getcwd())
        self.path_to_temp: str = os.path.join(root_path, 'temp')
        self.supplemental_step: bool = False

    def get_base_url(self) -> str:
        parsed_uri = urlparse(self.credentials['url'])
        base_url: str = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        return base_url

    def process_loan(self, loan_data):
        self.supplemental_step = False
        self.navigate_to_home()
        self.search_file(loan_data)
        if self.file_found:
            handles_count = self.browser.get_window_handles()
            if len(handles_count) > 1:
                self.browser.switch_window(handles_count[1])
                self.browser.close_window()
                self.browser.switch_window(self.browser.get_window_handles()[0])
            com.log_message('Validating file content', 'TRACE')
            self.validate_file_content(loan_data)
            self.compare_and_label_parties(loan_data)
            com.log_message('Checking parties from tempo')
            try:
                self.check_parties_tempo(loan_data)
            except:
                try:
                    self.browser.go_back()
                    self.browser.handle_alert()
                    self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
                except Exception as ex:
                    com.log_message('Bot failed to go back after failure', 'TRACE')
                    com.log_message(ex, 'TRACE')
                    traceback.print_exc()
                com.log_message('Bot failed to add/validate parties from tempo')
            com.log_message('Checking parties from pacer')
            try:
                self.check_parties_pacer(loan_data['pacer_data'])
            except Exception as ex:
                com.log_message('Error in check_party_pacer flow:', 'TRACE')
                com.log_message(str(ex), 'TRACE')
                traceback.print_exc()
                com.take_screenshot(self.browser, 'check_party_pacer_exception')
                com.log_DOM(self.browser)
        else:
            self.open_new_file()
            self.populate_new_file(loan_data)
            self.compare_and_label_parties(loan_data)
            try:
                self.add_parties(loan_data)
            except Exception as ex:
                try:
                    self.browser.go_back()
                    self.browser.handle_alert()
                    self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
                except Exception as e:
                    com.log_message('Bot failed to go back after failure', 'TRACE')
                    com.log_message(e, 'TRACE')
                    traceback.print_exc()
                com.log_message('Bot failed to add parties: ' + str(ex))
                traceback.print_exc()

        com.log_message('create_new_case', 'TRACE')
        try:
            self.create_new_case(loan_data)
        except Exception as ex:
            com.log_message('Error in create_new_case flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'create_new_case_exception')
            com.log_DOM(self.browser)

        com.log_message('upload_documents', 'TRACE')
        try:
            self.upload_documents(loan_data['files'], loan_data['doc_type'])
        except Exception as ex:
            com.log_message('Error in upload_documents flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'upload_documents_exception')
            com.log_DOM(self.browser)
        self.navigate_to_case(loan_data['ca_case_num'])

        com.log_message('add_entities', 'TRACE')
        try:
            self.add_entities(loan_data['pacer_data'], loan_data)
        except Exception as ex:
            com.log_message('Error in add_entities flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'add_entities_exception')
            com.log_DOM(self.browser)

        self.navigate_to_case(loan_data['ca_case_num'])
        com.log_message('compare_nopc_poc_to_ea_arm', 'TRACE')
        try:
            if 'escrow' in loan_data['doc_type']:
                self.compare_nopc_poc_to_escrow(loan_data)
            elif 'arm' in loan_data['doc_type']:
                self.compare_nopc_poc_to_arm(loan_data)
        except Exception as ex:
            com.log_message('Error in compare_nopc_poc_to_ea_arm flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'compare_nopc_poc_to_ea_arm_exception')
            com.log_DOM(self.browser)

        if loan_data['gen_supplemental_step']:
            com.log_message('gen_supplemental_step', 'TRACE')
            self.generate_supplemental_step_for_exceptions()
        self.navigate_to_case(loan_data['ca_case_num'])

        com.log_message('save_lines_for_docs', 'TRACE')
        try:
            self.save_lines_for_docs()
        except Exception as ex:
            com.log_message('Error in save_lines_for_docs flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'save_lines_for_docs_exception')
            com.log_DOM(self.browser)
        if self.supplemental_step:
            return

        # macro 7
        loan_data['close_1448'] = True
        com.log_message('complete_mortgage_payment_change_form', 'TRACE')
        try:
            if 'escrow' in loan_data['files']:
                data_ea = loan_data['files']['escrow']['data']
                self.complete_mortgage_payment_change_form('EA', data_ea)
            elif 'arm' in loan_data['files']:
                data_arm = loan_data['files']['arm']['data']
                self.complete_mortgage_payment_change_form('ARM', data_arm)
        except Exception as ex:
            com.log_message('Error in complete_mortgage_payment_change_form flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'comp_mort_pymt_chng_form_exception')
            com.log_DOM(self.browser)
            loan_data['close_1448'] = False

        com.log_message('case_sendout_generate_nopc and edit_nopc_document', 'TRACE')
        try:
            if len(loan_data['pacer_data']['Debtor']) > 1:
                filepath = self.case_sendout_generate_nopc(loan_data['pacer_data']['Debtor'][0],
                                                           loan_data['pacer_data']['Debtor'][1])
            else:
                filepath = self.case_sendout_generate_nopc(loan_data['pacer_data']['Debtor'][0])
            if filepath != '':
                nopc_draft_path = ''
                if 'escrow' in loan_data['files']:
                    nopc_draft_path = self.edit_nopc_document(filepath, loan_data['files']['escrow']['path'], 'escrow')
                elif 'arm' in loan_data['files']:
                    nopc_draft_path = self.edit_nopc_document(filepath, loan_data['files']['arm']['path'], 'arm')
                self.upload_document(nopc_draft_path, '354', True)
                com.log_message('NOPC Draft Uploaded to CaseAware')
                os.remove(nopc_draft_path)
        except Exception as ex:
            com.log_message('Error in generate_edit_nopc flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'generate_edit_nopc_exception')
            com.log_DOM(self.browser)
            loan_data['close_1448'] = False
        self.navigate_to_case(loan_data['ca_case_num'])

        com.log_message('create_bk_certificate_of_service', 'TRACE')
        try:
            self.create_bk_certificate_of_service_nopc()
        except Exception as ex:
            com.log_message('Error in create_bk_certificate_of_service flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'create_bk_certificate_of_service_exception')
            com.log_DOM(self.browser)
            loan_data['close_1448'] = False

        com.log_message('complete_arm_statement', 'TRACE')
        try:
            self.complete_arm_statement()
        except Exception as ex:
            com.log_message('Error in complete_arm_statement flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'complete_arm_statement_exception')
            com.log_DOM(self.browser)
            loan_data['close_1448'] = False

    def open_login(self):
        preferences = {
            'download.default_directory': self.path_to_temp,
            'plugins.always_open_pdf_externally': True,
            'download.directory_upgrade': True,
            'download.prompt_for_download': False
        }
        count = 1
        while count <= 3 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.credentials['url'], preferences=preferences, headless=True)
                self.browser.set_window_size(1920, 1080)
                if not self.browser.does_page_contain_element("//input[@name='usr']"):
                    if not self.browser.find_element("//input[@name='usr']").is_displayed():
                        com.log_message("Logging into CaseAware failed. Input field not found.", 'ERROR')
                        self.browser.capture_page_screenshot(
                            os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output',
                                         f'CaseAware_login_fail_{count}.png'))
                        return
                self.browser.input_text_when_element_is_visible("//input[@name='usr']", self.credentials['login'])
                self.browser.input_text_when_element_is_visible("//input[@name='pwd']", self.credentials['password'])
                self.browser.click_element_when_visible("//a[text()='Login']")
                com.wait_element(self.browser, '//b[text()="Welcome to the CaseAware® System!"]')
                self.is_site_available = self.browser.does_page_contain_element("//a[text()='Find File']")
                com.log_message('Bot successfully loged into CaseAware')
            except Exception as ex:
                com.log_message(f"Logging into CaseAware. Attempt #{count} failed", 'ERROR')
                com.log_message(str(ex))
                self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output',
                                                                  f'CaseAware_login_fail_{count}.png'))
                self.browser.close_browser()
            finally:
                count += 1

    def search_file(self, loan_data):
        com.log_message('Searching loan ' + str(loan_data['loan_number']))
        com.wait_element(self.browser, '//input[@name="filt_loan"]')
        self.browser.input_text_when_element_is_visible('//input[@name="filt_loan"]', loan_data['loan_number'])
        self.browser.click_element_when_visible('//a[text()="Find File"]')
        com.wait_element(self.browser, '//td[text()=" > File View"]', 15)
        is_file_opened = self.browser.does_page_contain_element('//td[text()=" > File View"]')
        is_page_text = self.browser.does_page_contain_element('//b[text()="Search Results"]')
        while not is_file_opened or is_page_text:
            is_file_opened = self.browser.does_page_contain_element('//td[text()=" > File View"]')
            is_page_text = self.browser.does_page_contain_element('//b[text()="Search Results"]')
            if not is_page_text:
                break
        if self.browser.does_page_contain_element('//td[text()=" > File View"]'):
            # TODO: check if loan number same in CaseAware
            com.log_message('File found by loan number')
            self.file_found = True
            return
        elif not self.browser.does_page_contain_element('//b[text()="Search Results"]'):
            com.log_message('File not found. Searching via address')
            com.wait_element(self.browser, '//input[@name="filt_loan"]')
            self.browser.input_text_when_element_is_visible('//input[@name="filt_loan"]', '')
            tmp_address = loan_data['property_address_1'].split(' ')
            tmp_address.pop()
            self.browser.input_text_when_element_is_visible('//input[@name="filt_p_addr1"]',
                                                            ' '.join(tmp_address) + '*')
            com.log_message(' > ' + loan_data['property_address_1'])
            com.log_message(' < ' + ' '.join(tmp_address) + '*')
            self.browser.click_element_when_visible('//a[text()="Find File"]')
            com.wait_element(self.browser, '//td[text()=" > File View"]', 15)
            is_file_opened = self.browser.does_page_contain_element('//td[text()=" > File View"]')
            is_page_text = self.browser.does_page_contain_element('//b[text()="Search Results"]')
            while not is_file_opened or is_page_text:
                is_file_opened = self.browser.does_page_contain_element('//td[text()=" > File View"]')
                is_page_text = self.browser.does_page_contain_element('//b[text()="Search Results"]')
                if not is_page_text:
                    break
            if self.browser.does_page_contain_element('//td[text()=" > File View"]'):
                # TODO: check if loan number same in CaseAware
                com.log_message('File found by address')
                self.file_found = True
                return
            elif not self.browser.does_page_contain_element('//b[text()="Search Results"]'):
                com.log_message('File not found')
                self.file_found = False
                return

    def open_new_file(self):
        self.browser.click_element_when_visible('//td[@align="center"]//a[text()="Files"]')
        self.browser.click_element_when_visible('//a[text()="New"]')
        com.log_message('New File creation in CaseAware')

    def populate_new_file(self, loan_data):
        com.wait_element(self.browser, '//select[@name="site_id"]')
        # self.browser.select_from_list_by_value('//select[@name="site_id"]', self.REF_SITE_MAPPING[loan_data['referral_site']])
        # New requirement:
        self.browser.select_from_list_by_value('//select[@name="site_id"]', '31')
        self.browser.click_element_when_visible('//a[text()="Pick Client"]')
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])
        self.browser.click_element_when_visible('//option[contains(text(),"Carrington Mortgage Services, LLC")]')
        self.browser.click_element_when_visible('//a[text()="Save"]')
        self.browser.switch_window(self.browser.get_window_handles()[0])
        self.browser.select_from_list_by_value('//select[@name="client_cd_id"]', str(433))

        self.browser.click_element_when_visible('//a[text()="Choose Beneficiary"]')
        time.sleep(1)
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])
        self.browser.input_text_when_element_is_visible('//input[@name="filt_nm"]', loan_data['vest_in_the_name_of'])
        self.browser.click_element_when_visible('//a[text()="Filter"]')
        self.browser.click_element_when_visible('//option')
        self.browser.click_element_when_visible('//a[text()="Save"]')
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[0])
        # Beneficiary - copy details from Tempo field Vest in the Name of and in CaseAware select choose beneficiary and paste the details into the Name search box and hit enter to search. Is the bank returned?
        # Yes - select it by double clicking
        # No - select New and paste the details into the Corp. Name field and Save (No new button)
        # TODO add new beneficiary flow:
        # click '//a[text() = "New"]'
        # switch window to pop-up
        # wait element '//textarea[@id="co_name"]'
        # input text to '//textarea[@id="co_name"]'
        # click save '//a[text()="Save"]'

        self.browser.select_from_list_by_value('//select[@name="loan_type_id"]',
                                               CaseAware.LOAN_TYPE_MAPPING[loan_data['loan_type']])
        self.browser.input_text_when_element_is_visible('//input[@name="loan_num"]', loan_data['loan_number'])
        self.browser.input_text_when_element_is_visible('//input[@name="prop_addr1"]', loan_data['property_address_1'])
        self.browser.input_text_when_element_is_visible('//input[@name="prop_addr2"]', loan_data['property_address_2'])
        self.browser.input_text_when_element_is_visible('//input[@name="prop_addr3"]', loan_data['property_address_3'])
        self.browser.input_text_when_element_is_visible('//input[@name="city"]', loan_data['city'])
        self.browser.select_from_list_by_value('//select[@name="state"]', loan_data['state'])
        self.browser.input_text_when_element_is_visible('//input[@name="zip"]', loan_data['zip_code'])
        self.browser.select_from_list_by_value('//select[@name="dwell_type_id"]', str(1))
        com.wait_element(self.browser, '//select[@id="county_id"]')
        time.sleep(5)
        county_ca = self.browser.get_selected_list_label('//select[@id="county_id"]')
        com.log_message(county_ca)
        if county_ca == '-- SELECT --' or county_ca.strip() == '':
            if loan_data['county'] != '':
                # populate from tempo if available
                self.browser.select_from_list_by_label('//select[@id="county_id"]', loan_data['county'].strip())
            else:
                self.email_exception('county', loan_data['loan_number'])
                try:
                    lbl_list = self.browser.get_list_items('//select[@id="county_id"]')
                    if len(lbl_list) > 1:
                        self.browser.select_from_list_by_index('//select[@id="county_id"]', '1')
                        if self.test_run:
                            self.browser.click_element_when_visible('//a[text()="Home"]')
                            self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
                        else:
                            self.browser.click_element_when_visible('//div[@id="save_new_del_top"]/a[text()="Save"]')
                            time.sleep(5)
                            self.browser.switch_window(self.browser.get_window_handles()[1])
                            com.wait_element(self.browser, '//a[text()="Save"]')
                            self.browser.click_element_when_visible('//a[text()="Save"]')
                            self.browser.switch_window(self.browser.get_window_handles()[0])
                except:
                    return
                return
        if self.test_run:
            self.browser.click_element_when_visible('//a[text()="Home"]')
            self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
        else:
            self.browser.click_element_when_visible('//div[@id="save_new_del_top"]/a[text()="Save"]')
            i = 0
            while i < 100:
                try:
                    self.browser.switch_window(self.browser.get_window_handles()[1])
                    com.wait_element(self.browser, '//a[text()="Save"]')
                    self.browser.click_element_when_visible('//a[text()="Save"]')
                    self.browser.switch_window(self.browser.get_window_handles()[0])
                    break
                except:
                    pass
                time.sleep(1)
                i += 1

    def check_parties_tempo(self, loan_data):
        com.wait_element(self.browser, '//a[@class="tabs_href"]/font[text()="Parties"]')
        com.take_screenshot(self.browser, "check_parties_tempo_1")
        self.browser.click_element_when_visible('//a[@class="tabs_href"]/font[text()="Parties"]')
        com.take_screenshot(self.browser, "check_parties_tempo_2")
        # get parties on CaseAware:
        com.wait_element(self.browser, '//td[text()=" > File Parties"]')
        com.wait_element(self.browser, '//td[@width="15%"]/a', 15)
        com.take_screenshot(self.browser, "check_parties_tempo_3")
        parties_on_caseaware = self.browser.find_elements('//td[@width="15%"]/a')
        for ca_party in parties_on_caseaware:
            for party in loan_data['parties']:
                if party['first_name'].lower() in ca_party.text.lower() and party['last_name'].lower() in ca_party.text.lower() and party['middle_name'].lower() in ca_party.text.lower():
                    party['status'] = 'to_validate'
        for party in loan_data['parties']:
            com.wait_element(self.browser, '//a[@class="tabs_href"]/font[text()="Parties"]')
            try:
                self.browser.click_element_when_visible('//a[@class="tabs_href"]/font[text()="Parties"]')
            except:
                pass
            if 'status' in party:
                if party['status'] == 'to_validate':
                    self.validate_party_tempo(party, loan_data['loan_number'])
            else:
                self.add_party_tempo(party, loan_data['loan_number'])
            if 'debtor' in party:
                self.add_debtor_to_tempo_party(party)
        com.log_message('Parties are valid')

    def validate_party_tempo(self, party_data, loan_number):
        com.log_message('Tempo Borrower in CaseAware Validation', 'TRACE')
        com.wait_element(self.browser, '//td[text()=" > File Parties"]')
        com.wait_element(self.browser, '//td[@width="15%"]/a', 15)
        com.take_screenshot(self.browser, "validate_party_tempo_1")
        is_need_to_save: bool = False
        temp_lname = party_data['last_name'].lower()
        temp_fname = party_data['first_name'].lower()
        temp_mname = party_data['middle_name'].lower()
        com.log_message(f'Searching for {temp_fname} {temp_lname} {temp_mname}', 'TRACE')
        party = self.browser.find_elements(
            f'//td[@width="15%"]/a[{com.contains_lower_xpath(temp_lname)} and {com.contains_lower_xpath(temp_fname)} and {com.contains_lower_xpath(temp_mname)}]')
        if len(party) > 0:
            party[0].click()
        else:
            com.log_message(f'No party fn:{temp_fname} ln:{temp_lname} found on UI')
            self.browser.go_back()
            try:
                self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
            except:
                pass
            return
        com.wait_element(self.browser, '//input[@id="fname"]')
        fname_ca = self.browser.find_element('//input[@id="fname"]').get_attribute('value').lower()
        mname_ca = self.browser.find_element('//input[@id="middle"]').get_attribute('value').lower()
        lname_ca = self.browser.find_element('//input[@id="lname"]').get_attribute('value').lower()
        address_1_ca = self.browser.find_element('//input[@id="addr1"]').get_attribute('value').lower()
        address_2_ca = self.browser.find_element('//input[@id="addr2"]').get_attribute('value').lower()
        address_3_ca = self.browser.find_element('//input[@id="addr3"]').get_attribute('value').lower()
        city_ca = self.browser.find_element('//input[@id="city"]').get_attribute('value').lower()
        state_ca = self.browser.get_selected_list_label('//select[@id="state"]').lower()
        zip_ca = self.browser.find_element('//input[@id="zip"]').get_attribute('value').lower()
        if fname_ca not in party_data['first_name'].lower() or fname_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="fname"]', party_data['first_name'])
            is_need_to_save = True
        if mname_ca not in party_data['middle_name'].lower() or mname_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="middle"]', party_data['middle_name'])
            is_need_to_save = True
        if lname_ca not in party_data['last_name'].lower() or lname_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="lname"]', party_data['last_name'])
            is_need_to_save = True
        if address_1_ca not in party_data['address_1'].lower() or address_1_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="addr1"]', party_data['address_1'])
            is_need_to_save = True
        if address_2_ca not in party_data['address_2'].lower() or address_2_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="addr2"]', party_data['address_2'])
            is_need_to_save = True
        if address_3_ca not in party_data['address_3'].lower() or address_3_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="addr3"]', party_data['address_3'])
            is_need_to_save = True
        if city_ca not in party_data['city'].lower() or city_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="city"]', party_data['city'])
            is_need_to_save = True
        if state_ca not in party_data['state'].lower() or state_ca == '':
            self.browser.select_from_list_by_value('//select[@id="state"]', party_data['state'])
            is_need_to_save = True
        if not self.check_both_ways_value(zip_ca, party_data['zip'].lower()) or zip_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="zip"]', party_data['zip'])
            is_need_to_save = True
        time.sleep(1)
        self.browser.set_focus_to_element('//select[@id="county_id"]')
        county_ca = self.browser.get_selected_list_label('//select[@id="county_id"]')
        com.take_screenshot(self.browser, "validate_party_tempo_2")
        if county_ca == '-- SELECT --' or county_ca.strip() == '':
            if party_data['county'].lower() != '':
                any_county_added = False
                try:
                    self.browser.select_from_list_by_label('//select[@id="county_id"]', party_data['county'].strip())
                    any_county_added = True
                except:
                    com.log_message('Failed to add county: ' + party_data['county'].strip())
                if not any_county_added:
                    try:
                        lbl_list = self.browser.get_list_items('//select[@id="county_id"]')
                        if len(lbl_list) > 1:
                            self.browser.select_from_list_by_index('//select[@id="county_id"]', '1')
                            self.email_exception('county', loan_number)
                    except:
                        com.log_message('Failed to first county from list')
            else:
                try:
                    lbl_list = self.browser.get_list_items('//select[@id="county_id"]')
                    if len(lbl_list) > 1:
                        self.browser.select_from_list_by_index('//select[@id="county_id"]', '1')
                        self.email_exception('county', loan_number)
                except:
                    com.log_message('Failed to first county from list')
        else:
            com.log_message('Validation tempo success', 'TRACE')
            changed_fields = self.browser.find_elements('//input[@style="background-color: rgb(241, 249, 255);"]')
            if len(changed_fields) > 0:
                is_need_to_save = True
            else:
                is_need_to_save = False
            party_data['status'] = 'validated'
        if self.test_run or not is_need_to_save:
            self.browser.go_back()
            try:
                com.take_screenshot(self.browser, "validate_party_tempo_3")
                self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
            except:
                pass
        else:
            self.browser.click_element_when_visible('//div[@id="save_new_del_top"]/a[text()="Save"]')
            try:
                self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
                self.browser.go_back()
                com.take_screenshot(self.browser, "validate_party_tempo")
                self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
            except:
                pass
            com.take_screenshot(self.browser, "validate_party_tempo_4")

    def add_parties(self, loan_data):
        self.compare_and_label_parties(loan_data)
        com.wait_element(self.browser, '//a[@class="tabs_href"]/font[text()="Parties"]')
        self.browser.click_element_when_visible('//a[@class="tabs_href"]/font[text()="Parties"]')
        for party in loan_data['parties']:
            self.add_party_tempo(party, loan_data['loan_number'])
            if 'debtor' in party:
                self.add_debtor_to_tempo_party(party)
        for party in loan_data['pacer_data']['Debtor']:
            if 'borrower' not in party:
                self.add_party_pacer(party)
        com.log_message('Parties added')

    def add_party_tempo(self, party_data, loan_number: str):
        com.wait_element(self.browser, '//a[text()="New"]')
        self.browser.click_element_when_visible('//a[text()="New"]')
        com.wait_element(self.browser, '//select[@id="fdid"]')
        self.browser.select_from_list_by_value('//select[@id="fdid"]', '1')
        self.browser.input_text_when_element_is_visible('//input[@id="fname"]', party_data['first_name'])
        self.browser.input_text_when_element_is_visible('//input[@id="middle"]', party_data['middle_name'])
        self.browser.input_text_when_element_is_visible('//input[@id="lname"]', party_data['last_name'])
        self.browser.input_text_when_element_is_visible('//input[@id="addr1"]', party_data['address_1'])
        self.browser.input_text_when_element_is_visible('//input[@id="addr2"]', party_data['address_2'])
        self.browser.input_text_when_element_is_visible('//input[@id="addr3"]', party_data['address_3'])
        self.browser.input_text_when_element_is_visible('//input[@id="city"]', party_data['city'])
        self.browser.select_from_list_by_value('//select[@id="state"]', party_data['state'])
        self.browser.input_text_when_element_is_visible('//input[@id="zip"]', party_data['zip'])
        self.browser.set_focus_to_element('//select[@id="county_id"]')
        time.sleep(5)
        # TODO refactor this part to get list of labeles in CA, check if any matches from tempo/pacer, select correct
        try:
            self.browser.select_from_list_by_label('//select[@id="county_id"]', party_data['county'])
        except:
            pass
        time.sleep(1)
        county_ca = self.browser.get_selected_list_label('//select[@id="county_id"]')
        if county_ca == '-- SELECT --' or county_ca.strip() == '':
            try:
                self.email_exception('county', loan_number)
                lbl_list = self.browser.get_list_items('//select[@id="county_id"]')
                if len(lbl_list) > 1:
                    self.browser.select_from_list_by_index('//select[@id="county_id"]', '1')
                    if self.test_run:
                        self.browser.go_back()
                    else:
                        self.browser.click_element_when_visible('//div[@id="save_new_del_top"]/a[text()="Save"]')
                    party_data['status'] = 'added'
            except Exception as ex:
                com.log_message('Error in add_tempo_party flow:', 'TRACE')
                com.log_message(str(ex), 'TRACE')
                traceback.print_exc()
                com.take_screenshot(self.browser, 'complete_arm_statement_exception')
                com.log_DOM(self.browser)
        else:
            if self.test_run:
                self.browser.go_back()
            else:
                self.browser.click_element_when_visible('//div[@id="save_new_del_top"]/a[text()="Save"]')
            party_data['status'] = 'added'

    def add_debtor_to_tempo_party(self, party_data):
        com.log_message('Add debtor role to Tempo Borrower in CaseAware')
        com.wait_element(self.browser, '//td[text()=" > File Parties"]')
        com.wait_element(self.browser, '//td[@width="15%"]/a', 15)
        com.take_screenshot(self.browser, "validate_party_tempo_1")
        temp_lname = party_data['last_name'].lower()
        temp_fname = party_data['first_name'].lower()
        com.log_message(f'Searching for {temp_fname} {temp_lname}', 'TRACE')
        party = self.browser.find_elements(
            f'//td[@width="15%"]/a[{com.contains_lower_xpath(temp_lname)} and {com.contains_lower_xpath(temp_fname)}]')
        if len(party) > 0:
            party[0].click()
        else:
            com.log_message(f'No party fn:{temp_fname} ln:{temp_lname} found on UI')
            self.browser.go_back()
            try:
                self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
            except:
                pass
            return
        com.wait_element(self.browser, '//select[@id="fdid"]')
        if self.browser.is_element_visible('//select[@id="fdid"]'):
            self.browser.select_from_list_by_value('//select[@id="fdid"]', str(7))
            time.sleep(1)
            if self.test_run:
                self.browser.go_back()
                try:
                    com.take_screenshot(self.browser, "validate_party_pacer_3")
                    self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
                except:
                    pass
            else:
                try:
                    com.take_screenshot(self.browser, "validate_party_pacer_4")
                    self.browser.click_element_when_visible('//a[text()="Save"]')
                    self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
                    com.take_screenshot(self.browser, "validate_party_pacer_5")
                except:
                    pass
                try:
                    self.browser.switch_window(self.browser.get_window_handles()[1])
                    self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
                    self.browser.switch_window(self.browser.get_window_handles()[0])
                    com.take_screenshot(self.browser, "validate_party_pacer_6")
                except:
                    self.browser.switch_window(self.browser.get_window_handles()[0])
                    self.browser.go_back()
                    try:
                        com.take_screenshot(self.browser, "validate_party_pacer_3")
                        self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
                    except:
                        pass

    def create_new_case(self, loan_data):
        com.log_message('Creating New Case')
        com.take_screenshot(self.browser, "create_new_case_1")
        com.wait_element(self.browser, '//a/font[text()="View File"]')
        try:
            self.browser.click_element_when_visible('//a/font[text()="View File"]')
        except:
            self.browser.go_back()
            com.wait_element(self.browser, '//a/font[text()="View File"]')
            self.browser.click_element_when_visible('//a/font[text()="View File"]')
        com.wait_element(self.browser, '//tr/td/b[contains(text(), "Cases")]/following-sibling::div/a')
        self.browser.click_element_when_visible('//tr/td/b[contains(text(), "Cases")]/following-sibling::div/a')
        com.wait_element(self.browser, '//div[@class="page-title" and contains(text(), "Cases Edit")]')
        com.wait_element(self.browser, '//select[@id="atty_id"]')
        com.take_screenshot(self.browser, "create_new_case_2")
        self.browser.select_from_list_by_value('//select[@id="atty_id"]', self.ATTORNEY_VALUE_MAPPING[
            self.ATTORNEY_STATE_MAPPING[loan_data['referral_site']]['user_list'][
                self.ATTORNEY_STATE_MAPPING[loan_data['referral_site']]['last_used_id']]])
        self.browser.select_from_list_by_value('//select[@id="user_id"]', self.ATTORNEY_VALUE_MAPPING[
            self.ATTORNEY_STATE_MAPPING[loan_data['referral_site']]['user_list'][
                self.ATTORNEY_STATE_MAPPING[loan_data['referral_site']]['last_used_id']]])
        self.ATTORNEY_STATE_MAPPING[loan_data['referral_site']]['last_used_id'] += 1
        if self.ATTORNEY_STATE_MAPPING[loan_data['referral_site']]['last_used_id'] > len(
                self.ATTORNEY_STATE_MAPPING[loan_data['referral_site']]['user_list']) - 1:
            self.ATTORNEY_STATE_MAPPING[loan_data['referral_site']]['last_used_id'] = 0
        self.browser.select_from_list_by_value('//select[@id="case_type_id"]', str(3))
        self.browser.select_from_list_by_value('//select[@id="case_seq_id"]', str(228))
        com.take_screenshot(self.browser, "create_new_case_3")
        pacer_bp = re.split(r'-\D{3}', loan_data['pacer_data']['Bankruptcy Petition #'])[0]
        self.browser.input_text_when_element_is_visible('//input[@id="flex_10"]', pacer_bp)
        if self.test_run:
            return
        self.browser.click_element_when_visible('//div[@id="save_new_del_top"]/a[text()="Save"]')
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])
        try:
            self.browser.click_element_when_visible('//a[text()="Save"]')
        except Exception as e:
            com.log_message('Unexpected window appeared and closed: ' + str(e), 'TRACE')
            time.sleep(1)
            browser_tabs = self.browser.get_window_handles()
            self.browser.switch_window(browser_tabs[1])
            self.browser.click_element_when_visible('//a[text()="Save"]')
            time.sleep(1)
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[0])
        com.log_message('New Case Created')
        # go to 'Edit Case'
        com.log_message('Adding Chapter and Claim Number to created case', 'TRACE')
        self.browser.click_element_when_visible('//a/font[text()="Edit Case"]')
        com.wait_element(self.browser, '//div[@class="page-title"]')
        self.browser.select_from_list_by_value('//select[@id="flex_11"]', str(13))
        try:
            self.browser.input_text_when_element_is_visible('//input[@id="flex_15"]', loan_data['claim_no'])
        except:
            com.log_message('Can not add claim number. Not identified', 'TRACE')
        # get case number for later stages:
        try:
            loan_data['ca_case_num'] = self.browser.find_element('//input[@id="case_num"]').get_attribute("value")
        except Exception as ex:
            com.log_message(str(ex))
        self.browser.click_element_when_visible('//a[@class="button" and text()="Save"]')
        com.log_message('Chapter and Claim Number added to created case')
        time.sleep(5)

    def add_entities(self, pacer_data, loan_data):
        com.wait_element(self.browser, '//a/font[text()="View File"]')
        try:
            self.browser.click_element_when_visible('//a/font[text()="View File"]')
        except:
            try:
                self.browser.click_element_when_visible('//a[@class="button" and text()="Save"]')
                self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
            except:
                pass
            try:
                self.browser.go_back()
                self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
            except:
                pass
            com.wait_element(self.browser, '//a/font[text()="View File"]')
            self.browser.click_element_when_visible('//a/font[text()="View File"]')
        com.take_screenshot(self.browser, "add_entities")
        try:
            self.remove_prepopulated_bk_if_any()
        except Exception as ex:
            com.log_message('Unable to remove BK entities: ' + str(ex), 'TRACE')
        self.navigate_to_case(loan_data['ca_case_num'])
        try:
            self.add_court(pacer_data['Court Name'], loan_data['loan_number'])
        except Exception as ex:
            com.log_message('Error in add_court flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'add_court_exception')
            com.log_DOM(self.browser)
        self.navigate_to_case(loan_data['ca_case_num'])
        try:
            self.add_judge(pacer_data['Assigned to'], loan_data['loan_number'])
        except Exception as ex:
            com.log_message('Error in add_judge flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'add_judge_exception')
            com.log_DOM(self.browser)
        self.navigate_to_case(loan_data['ca_case_num'])
        try:
            self.add_trustee(pacer_data, loan_data['loan_number'])
        except Exception as ex:
            com.log_message('Error in add_trustee flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'add_trustee_exception')
            com.log_DOM(self.browser)
        self.navigate_to_case(loan_data['ca_case_num'])
        try:
            self.add_debtor_attorney(pacer_data, loan_data['loan_number'])
        except Exception as ex:
            com.log_message('Error in add_debtor_attorney flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'add_debtor_attorney_exception')
            com.log_DOM(self.browser)
        self.navigate_to_case(loan_data['ca_case_num'])
        try:
            self.add_us_trustee(pacer_data, loan_data['loan_number'])
        except Exception as ex:
            com.log_message('Error in add_us_trustee flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'add_us_trustee_exception')
            com.log_DOM(self.browser)

    def add_court(self, court_name, loan_number):
        com.log_message('Adding court', 'TRACE')
        com.take_screenshot(self.browser, "add_court_1")
        com.wait_element(self.browser, '//a/font[text()="Entities"]')
        com.take_screenshot(self.browser, "add_court_2")
        self.browser.click_element_when_visible('//a/font[text()="Entities"]')
        com.wait_element(self.browser, '//td[contains(text(),"File Entities")]')
        com.take_screenshot(self.browser, "add_court_3")
        self.browser.click_element_when_visible('//a[text()="Add"]')
        com.wait_element(self.browser, '//td[contains(text(),"File Entity Add/Remove")]')
        court_parts = court_name.replace('.', '').split(' ')
        res = self.find_and_pick_unchecked_checkbox(court_parts)
        if res:
            com.log_message('Court Added to CaseAware')
        else:
            com.log_message('Court not Added to CaseAware')
            self.email_exception('court', loan_number)
        com.take_screenshot(self.browser, "add_court_6")
        save_btn = self.browser.does_page_contain_element('//a[text()="Filter"]/preceding-sibling::a[text()="Save"]')
        if save_btn:
            if self.browser.is_element_visible('//a[text()="Filter"]/preceding-sibling::a[text()="Save"]'):
                try:
                    self.browser.click_element_when_visible('//a[text()="Filter"]/preceding-sibling::a[text()="Save"]')
                except:
                    com.log_message('No Save button', 'TRACE')
                    com.take_screenshot(self.browser, 'no_save_button_exception')
        else:
            com.log_message('There is no save button available', 'TRACE')
            com.take_screenshot(self.browser, 'no_save_button')
        try:
            com.take_screenshot(self.browser, "add_court_7")
            self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
        except Exception as ex:
            try:
                self.browser.handle_alert()
            except:
                pass
            com.log_message(ex)

    def add_judge(self, judge_name, loan_number):
        com.log_message('Adding judge', 'TRACE')
        com.take_screenshot(self.browser, "add_judge_1")
        is_judge_added = False
        if len(self.browser.get_window_handles()) > 1:
            try:
                self.browser.switch_window(self.browser.get_window_handles()[1])
                com.take_screenshot(self.browser, "add_judge_2")
                judge_name_split = judge_name.replace('.', '').split(' ')
                match_num = len(judge_name_split)
                judges = self.browser.find_elements('//tr[@clase="small"]')  # do not change this typo
                judges_to_uncheck = []
                for judge in judges:
                    match_counter = 0
                    for part_name in judge_name_split:
                        if part_name in judge.text:
                            match_counter += 1
                    if match_counter != match_num:
                        judges_to_uncheck.append(judges.index(judge))
                checkboxes = self.browser.find_elements('//tr[@clase="small"]/td/input')
                try:
                    com.log_message(str(len(judges)) + ' found VS. ' + str(len(judges_to_uncheck)) + ' to uncheck',
                                    'TRACE')
                except:
                    com.log_message(len(judges))
                    com.log_message(len(judges_to_uncheck))
                for index in judges_to_uncheck:
                    checkboxes[index].click()
                com.take_screenshot(self.browser, "add_judge_3")
                self.browser.click_element_when_visible('//a[contains(text(),"Add")]')
                is_judge_added = True
                try:
                    self.browser.alert_should_not_be_present()
                except:
                    is_judge_added = False
                if len(judges_to_uncheck) == len(judges):
                    raise Exception
                com.take_screenshot(self.browser, "add_judge_4")
                com.log_message('Judge Added to CaseAware')
                self.browser.switch_window(self.browser.get_window_handles()[0])
                com.take_screenshot(self.browser, "add_judge_5")
            except:
                is_judge_added = False
                try:
                    self.browser.switch_window(self.browser.get_window_handles()[0])
                except:
                    com.log_message('Unable to switch windows', 'TRACE')
        if not is_judge_added:
            com.log_message("There is no 'Add judge' pop-up window. Searching manually", 'TRACE')
            com.take_screenshot(self.browser, "add_judge_1")
            self.browser.click_element_when_visible('//a/font[text()="Entities"]')
            com.wait_element(self.browser, '//td[contains(text(),"File Entities")]')
            com.take_screenshot(self.browser, "add_judge_2")
            self.browser.click_element_when_visible('//a[text()="Add"]')
            com.wait_element(self.browser, '//td[contains(text(),"File Entity Add/Remove")]')
            com.take_screenshot(self.browser, "add_judge_3")
            self.browser.select_from_list_by_value('//select[@name="filt_ent_cat_id"]', str(7))
            name_parts = judge_name.replace('.', '').split(' ')
            res = self.find_and_pick_unchecked_checkbox(name_parts)
            if res:
                com.log_message('Judge Added to CaseAware')
            else:
                com.log_message('Judge not Added to CaseAware')
                self.email_exception('judge', loan_number)

    def add_trustee(self, pacer_data, loan_number):
        com.log_message('Adding trustee', 'TRACE')
        com.take_screenshot(self.browser, "add_trustee_attorney_1")
        self.browser.click_element_when_visible('//a/font[text()="Entities"]')
        com.wait_element(self.browser, '//td[contains(text(),"File Entities")]')
        com.take_screenshot(self.browser, "add_trustee_attorney_2")
        self.browser.click_element_when_visible('//a[text()="Add"]')
        com.wait_element(self.browser, '//td[contains(text(),"File Entity Add/Remove")]')
        com.take_screenshot(self.browser, "add_trustee_attorney_3")
        self.browser.select_from_list_by_value('//select[@name="filt_ent_cat_id"]', str(8))
        name_parts = pacer_data['Trustee'][0].replace('.', ' ').split(' ')
        res = self.find_and_pick_unchecked_checkbox(name_parts)
        if res:
            com.log_message('Trustee added')
        else:
            com.log_message('Trustee was not added')
            com.log_message('No trustee checkbox', 'ERROR')
            self.email_exception('trustee', loan_number)

    def add_debtor_attorney(self, pacer_data, loan_number):
        com.log_message('Adding debtor attorney', 'TRACE')
        com.wait_element(self.browser, '//a/font[text()="Entities"]')
        com.take_screenshot(self.browser, "add_trustee_attorney_7")
        self.browser.click_element_when_visible('//a/font[text()="Entities"]')
        com.wait_element(self.browser, '//td[contains(text(),"File Entities")]')
        com.take_screenshot(self.browser, "add_trustee_attorney_8")
        self.browser.click_element_when_visible('//a[text()="Add"]')
        com.wait_element(self.browser, '//td[contains(text(),"File Entity Add/Remove")]')
        com.take_screenshot(self.browser, "add_trustee_attorney_9")
        self.browser.select_from_list_by_value('//select[@name="filt_ent_cat_id"]', str(32))
        name_parts = pacer_data['Debtor Attorney'].replace('.', '').split(' ')
        address_parts = self.get_correct_address(pacer_data["Debtor Attorney other"])
        nice_address = address_parts['addr']
        res = self.find_and_pick_unchecked_checkbox(name_parts, True, nice_address)
        if res:
            com.log_message('Debtor Attorney added')
            try:
                self.validate_datty_address(name_parts, pacer_data['Debtor Attorney other'])
            except:
                try:
                    self.browser.go_back()
                    self.browser.handle_alert()
                except:
                    com.log_message('Bot was not able to go back after saving Debtor Attorney address', 'TRACE')
                com.log_message('Failed to validate Debtor Attorney Address')
        else:
            com.log_message('Debtor Attorney was not added')
            com.log_message('No Debtor Attorney checkbox', 'ERROR')
            self.email_exception('debtor_attorney', loan_number)

    def add_us_trustee(self, pacer_data, loan_number):
        if 'U.S. Trustee' in pacer_data:
            com.log_message('Adding us trustee')
            com.wait_element(self.browser, '//a/font[text()="Entities"]')
            self.browser.click_element_when_visible('//a/font[text()="Entities"]')
            com.wait_element(self.browser, '//td[contains(text(),"File Entities")]')
            self.browser.click_element_when_visible('//a[text()="Add"]')
            com.wait_element(self.browser, '//td[contains(text(),"File Entity Add/Remove")]')
            self.browser.select_from_list_by_value('//select[@name="filt_ent_cat_id"]', str(39))
            name_parts = pacer_data['U.S. Trustee'].split(' ')
            address_parts = self.get_correct_address(pacer_data['U.S. Trustee other'])
            nice_address = address_parts['addr']
            res = self.find_and_pick_unchecked_checkbox(name_parts, True, nice_address)
            if res:
                com.log_message('U.S. Trustee added')
            else:
                com.log_message('U.S. Trustee was not added')
                com.log_message('No us trustee checkbox', 'ERROR')
                self.email_exception('us_trustee', loan_number)
        else:
            com.log_message('U.S. trustee not in pacer docket', 'TRACE')

    def find_and_pick_unchecked_checkbox(self, name_parts: list, is_address: bool = False, address=None) -> bool:
        com.wait_element(self.browser, '//input[@name="filt_name"]')
        cb_should_contain = ''
        for np in name_parts:
            if cb_should_contain != '':
                cb_should_contain += ' and '
            cb_should_contain += com.contains_lower_xpath(np.strip(), '.')
        cb_should_contain_addr = ''
        if is_address:
            addr_parts = address.lower().split(' ')
            for ap in addr_parts:
                if cb_should_contain_addr != '':
                    cb_should_contain_addr += ' and '
                cb_should_contain_addr += com.contains_lower_xpath(ap.strip(), '.')
        com.log_message('Searching for:', 'TRACE')
        com.log_message(str(name_parts), 'TRACE')
        com.log_message('nice look:', 'TRACE')
        com.log_message(str(cb_should_contain), 'TRACE')
        if is_address:
            com.log_message(str(address.lower().split(' ')), 'TRACE')
            com.log_message('nice look:', 'TRACE')
            com.log_message(str(cb_should_contain_addr), 'TRACE')
        for np in name_parts:
            self.browser.input_text_when_element_is_visible('//input[@name="filt_name"]', '')
            self.browser.input_text_when_element_is_visible('//input[@name="filt_name"]', "*" + np + "*")
            self.browser.driver.find_elements_by_xpath('//input[@name="filt_name"]')[0].send_keys(Keys.ENTER)
            com.wait_element(self.browser,
                             f'//td[a[{cb_should_contain}]]/preceding-sibling::td/input[@type="checkbox"]')
            # com.take_screenshot(self.browser, "add_trustee_attorney_5")
            # all_addresses = self.browser.find_elements('//div[@id="lst_grid_dtls_div"]//tr/td[5]')
            # all_names = self.browser.find_elements('//div[@id="lst_grid_dtls_div"]//tr/td[3]/a')
            # all_cb = self.browser.find_elements('//div[@id="lst_grid_dtls_div"]//tr/td[1]/input[@type="checkbox"]')
            # for tmp in all_addresses.copy():
            #     if 'Address, City, State, Zip' in tmp.text:
            #         all_addresses.remove(tmp)
            # i = 0
            checkbox = []
            com.log_message(len(checkbox), 'TRACE')
            if is_address:
                com.log_message('Searching checkbox using address', 'TRACE')
                com.log_message(f'//td[{cb_should_contain}]/following-sibling::td[{cb_should_contain_addr}]/preceding-sibling::td/input[@type="checkbox"]', 'TRACE')
                checkbox = self.browser.find_elements(
                    f'//td[{cb_should_contain}]/following-sibling::td[{cb_should_contain_addr}]/preceding-sibling::td/input[@type="checkbox"]')
            else:
                com.log_message('Searching checkbox NOT using address', 'TRACE')
                com.log_message(f'//td[a[{cb_should_contain}]]/preceding-sibling::td/input[@type="checkbox"]', 'TRACE')
                checkbox = self.browser.find_elements(
                    f'//td[a[{cb_should_contain}]]/preceding-sibling::td/input[@type="checkbox"]')
            com.log_message(len(checkbox), 'TRACE')
            if len(checkbox) > 0:
                if is_address:
                    is_selected = self.browser.is_checkbox_selected(
                        f'//td[{cb_should_contain}]/following-sibling::td[{cb_should_contain_addr}]/preceding-sibling::td/input[@type="checkbox"]')
                else:
                    is_selected = self.browser.is_checkbox_selected(
                        f'//td[a[{cb_should_contain}]]/preceding-sibling::td/input[@type="checkbox"]')
                com.log_message(is_selected, 'TRACE')
                if not is_selected:
                    checkbox[0].click()
                    com.log_message('Entity added', 'TRACE')
                    self.browser.click_element_when_visible('//a[text()="Filter"]/preceding-sibling::a[text()="Save"]')
                else:
                    com.log_message('Entity already added', 'TRACE')
                return True
            else:
                com.take_screenshot(self.browser, "add_entity_cb")
                com.log_message('No entity checkbox', 'TRACE')
                continue
        return False

    def compare_nopc_poc_to_escrow(self, loan_data: dict):
        data_from_escrow_analysis = loan_data['files']['escrow']['data']
        if 'nopc' in loan_data['doc_type']:
            # NOPC processing
            value_from_nopc_or_poc = loan_data['files']['nopc']['data']['new_escrow_payment']
        else:
            # POC processing
            value_from_nopc_or_poc = loan_data['files']['poc']['data']['monthly_escrow']

            # comparison of amounts
        escrow_payment_as_float = decimal.Decimal(data_from_escrow_analysis["current escrow payment"])
        try:
            shortage_pymt_as_float = decimal.Decimal(data_from_escrow_analysis["shortage_pymt_curr"])
        except Exception as ex:
            com.log_message(str(ex))
            shortage_pymt_as_float = decimal.Decimal("0.00")
        try:
            surplus_pymt_as_float = decimal.Decimal(data_from_escrow_analysis["surplus_pymt_curr"])
        except Exception as ex:
            com.log_message(str(ex))
            surplus_pymt_as_float = decimal.Decimal("0.00")
        value_from_nopc_or_poc_as_float = decimal.Decimal(value_from_nopc_or_poc)

        if escrow_payment_as_float + shortage_pymt_as_float + surplus_pymt_as_float == value_from_nopc_or_poc_as_float:
            com.log_message('ESCROW and NOPC/POC sum correct')
            calc_result: bool = self.calculate_remainder_days_to_due_date(data_from_escrow_analysis["due date"]) > 20
            if not calc_result:
                com.log_message('DAYS not correct')
                com.log_message(
                    str(self.calculate_remainder_days_to_due_date(data_from_escrow_analysis["due date"])) + ' > 20')
                self.generate_supplemental_step_for_exceptions()
            com.log_message('DAYS correct')
        else:
            com.log_message('ESCROW and NOPC/POC sum NOT correct')
            com.log_message(str(escrow_payment_as_float + shortage_pymt_as_float + surplus_pymt_as_float) + ' = ' + str(
                value_from_nopc_or_poc_as_float))
            self.generate_supplemental_step_for_exceptions()

    def compare_nopc_poc_to_arm(self, loan_data: dict):
        data_from_arm_change = loan_data['files']['arm']['data']
        if 'nopc' in loan_data['doc_type']:
            # NOPC processing
            nopc_total = loan_data['files']['nopc']['data']['new_total_payment']
            nopc_escrow = loan_data['files']['nopc']['data']['new_escrow_payment']
            value_from_nopc_or_poc = str(decimal.Decimal(nopc_total) - decimal.Decimal(nopc_escrow))
        else:
            # POC processing
            value_from_nopc_or_poc = loan_data['files']['poc']['data']['principal_and_interest']

        # comparison of amounts
        principal_payment_as_float = decimal.Decimal(data_from_arm_change["current principal"])
        interest_payment_as_float = decimal.Decimal(data_from_arm_change["current interest"])
        principal_plus_interest_payment_as_float = principal_payment_as_float + interest_payment_as_float

        value_from_nopc_or_poc_as_float = decimal.Decimal(value_from_nopc_or_poc)
        if principal_plus_interest_payment_as_float == value_from_nopc_or_poc_as_float:
            calc_result: bool = self.calculate_remainder_days_to_due_date(data_from_arm_change["due date"]) > 20
            if not calc_result:
                self.generate_supplemental_step_for_exceptions()
        else:
            self.generate_supplemental_step_for_exceptions()

    def save_lines_for_docs(self):
        self.browser.click_element_when_visible('//font[contains(text(),"View Case")]')
        com.wait_element(browser=self.browser,
                         locator="//*[@id='lst_grid_tbl']//tbody//tr//td//table//tbody//tr//td[contains(text(), 'Case View: ')]")

        self.set_today_and_save("Review Referral")
        com.log_message('"Review Referral" Step Complete with Date')
        self.set_today_and_save("Obtain Documents")
        com.log_message('"Obtain Documents" Step Complete with Date')

    def set_today_and_save(self, description_substring):
        try:
            com.wait_element(self.browser, f"//td[contains(text(), '{description_substring}')]//following-sibling::td//font//a[text()='Today']")
            self.browser.click_element_when_visible(
                f"//td[contains(text(), '{description_substring}')]//following-sibling::td//font//a[text()='Today']")

            if self.test_run:
                com.log_message("dev_mode")
                self.browser.highlight_elements(
                    f"//td[contains(text(), '{description_substring}')]//following-sibling::td//a[text()='Save']",
                    style="solid", width="3px", color="yellow")
            else:
                pass
                self.browser.click_element_when_visible(
                    f"//td[contains(text(), '{description_substring}')]//following-sibling::td//a[text()='Save']")

        except Exception as ex:
            raise Exception("Error set today and save. " + str(ex))

    @staticmethod
    def calculate_remainder_days_to_due_date(due_date: str) -> int:
        due_date_as_date_type = datetime.strptime(due_date, "%m/%d/%y").date()
        return (due_date_as_date_type - datetime.today().date()).days

    def generate_supplemental_step_for_exceptions(self):
        com.log_message('Generating supplemental step', 'TRACE')
        self.browser.click_element_when_visible('//font[contains(text(),"View Case")]')
        com.wait_element(self.browser, '//a[contains(text(),"Supplemental") and @class="button"]')

        self.browser.click_element_when_visible('//a[contains(text(),"Supplemental") and @class="button"]')
        com.wait_element(self.browser,
                         '//table[@id="lst_grid_dtls_tbl"]//tbody//tr//td[contains(text(), "BK Attorney Review EA/ARM")]')

        self.browser.click_element_when_visible(
            '//table[@id="lst_grid_dtls_tbl"]//tbody//tr//td[contains(text(), "BK Attorney Review EA/ARM")]//preceding-sibling::td//input[@type ="checkbox"]')

        self.supplemental_step = True

        if self.test_run:
            self.browser.highlight_elements(locator='//a[contains(text(),"Save") and @class="button"]', width="2px",
                                            style="solid")
        else:
            self.browser.click_element_when_visible('//a[contains(text(),"Save") and @class="button"]')
        com.log_message('Supplemental Step Completed')

    def upload_document(self, path_to_doc, category_document: str, is_single_or_last: bool):
        is_upload_success = False
        retry_counter = 0
        while not is_upload_success and retry_counter < 3:
            try:
                try:
                    if not self.browser.is_element_visible('//input[@type="file"]'):
                        com.wait_element(self.browser, '//font[contains(text(),"Case Docs")]')
                        self.browser.click_element_when_visible('//font[contains(text(),"Case Docs")]')
                        com.wait_element(self.browser, '//a[contains(text(),"New Document") and @class="button"]')
                        self.browser.click_element_when_visible(
                            '//a[contains(text(),"New Document") and @class="button"]')
                except Exception as ex:
                    com.log_message(str(ex))
                    try:
                        com.wait_element(self.browser, '//font[contains(text(),"Case Docs")]')
                        self.browser.click_element_when_visible('//font[contains(text(),"Case Docs")]')
                        com.wait_element(self.browser, '//a[contains(text(),"New Document") and @class="button"]')
                        self.browser.click_element_when_visible(
                            '//a[contains(text(),"New Document") and @class="button"]')
                    except:
                        pass
                com.wait_element(self.browser, '//input[@type="file"]')

                self.browser.input_text_when_element_is_visible('//input[@type="file"]', path_to_doc)
                com.wait_element(self.browser, '//input[@name="send_msg"]')
                self.browser.click_element_when_visible(
                    '//input[@name="send_msg"]')  # (or change to uncheck if not stable)
                com.wait_element(self.browser, '//select[@id="doc_cat_id"]')
                self.browser.select_from_list_by_value('//select[@id="doc_cat_id"]', category_document)

                self.browser.click_element_when_visible(
                    '//td/input[@id="orig_dt"]/following-sibling::font[@class="tiny"]/a[text()="Today"]')
                self.browser.click_element_when_visible(
                    '//td/input[@id="recv_dt"]/following-sibling::font[@class="tiny"]/a[text()="Today"]')

                should_retry = False
                if self.test_run:
                    if is_single_or_last:
                        self.browser.highlight_elements(locator='//a[text()="Save"]', width="3px", style="solid")
                    else:
                        self.browser.highlight_elements(locator='//a[text()="Save and New"]', width="3px",
                                                        style="solid")

                    self.browser.go_back()
                else:
                    if is_single_or_last:
                        self.browser.click_element_when_visible('//a[text()="Save"]')
                        try:
                            self.browser.handle_alert()
                            should_retry = True
                        except:
                            pass
                    else:
                        self.browser.click_element_when_visible('//a[text()="Save and New"]')
                        try:
                            self.browser.handle_alert()
                            should_retry = True
                        except:
                            pass
                if should_retry:
                    raise Exception
                com.log_message(f'{path_to_doc} - uploaded successfully')
                is_upload_success = True
            except Exception as ex:
                raise Exception(f"Failure upload file {path_to_doc} . {str(ex)}")
            finally:
                retry_counter += 1

    def upload_documents(self, files, doc_type):
        com.log_message('Uploading documents', 'TRACE')
        if 'nopc' in doc_type and files['nopc']['downloaded']:
            self.upload_document(files['nopc']['path'], self.UPLOAD_DOC_MAPPING['Bankruptcy Documents'], False)
        if 'poc' in doc_type and files['poc']['downloaded']:
            self.upload_document(files['poc']['path'], self.UPLOAD_DOC_MAPPING['POC'], False)
        if 'escrow' in doc_type:
            if files['escrow']['downloaded']:
                self.upload_document(files['escrow']['path'], self.UPLOAD_DOC_MAPPING['Escrow Breakdown'], False)
        if 'arm' in doc_type:
            if files['arm']['downloaded']:
                self.upload_document(files['arm']['path'], self.UPLOAD_DOC_MAPPING['ARM Change'], False)
        if 'pacer' in files:
            self.upload_document(files['pacer']['path'], self.UPLOAD_DOC_MAPPING['Docket'], False)
        if 'claims' in files:
            self.upload_document(files['claims']['path'], self.UPLOAD_DOC_MAPPING['Bankruptcy Documents'], False)
        com.log_message("Documents Uploaded")

    @staticmethod
    def edit_nopc_document(path_to_doc, param_pdf, doc_type):
        pdfs = []
        final_pdf_path = os.path.join(os.path.abspath(os.path.dirname(path_to_doc)), 'NOPC_Draft.pdf')
        merger = PdfFileMerger()
        pdf_1 = ''
        if 'escrow' in doc_type:
            pdf_1 = word.process_document(path_to_doc, 'y', 'n', 'n')
        elif 'arm' in doc_type:
            pdf_1 = word.process_document(path_to_doc, 'n', 'y', 'n')
        pdfs.append(pdf_1)
        pdfs.append(param_pdf)
        for pdf in pdfs:
            merger.append(pdf)
        merger.write(final_pdf_path)
        merger.close()
        os.remove(pdf_1)
        return final_pdf_path

    def complete_arm_statement(self):
        self.browser.click_element_when_visible('//font[contains(text(),"View Case")]')
        self.set_today_and_save("Prepare ARM Statement")
        com.log_message('ARM Statement Task Completed in CaseAware')

    def close_logout(self):
        self.is_site_available = False
        try:
            self.browser.click_element_when_visible('//li[@class="has-sub"]/a[contains(text(), ", ")]')
            com.wait_element(self.browser, '//li[@class="has-sub"]/ul/li/a[text()="Logout"]')
            self.browser.click_element_when_visible('//li[@class="has-sub"]/ul/li/a[text()="Logout"]')
            time.sleep(1)
            try:
                self.browser.handle_alert()
            except:
                pass
            self.browser.close_window()
        except:
            pass
        com.log_message('Logged out', 'TRACE')

    def check_parties_pacer(self, pacer_data: dict):
        com.take_screenshot(self.browser, "check_parties_pacer_1")
        self.browser.click_element_when_visible('//a[@class="tabs_href"]/font[text()="Parties"]')
        # get parties on CaseAware:
        com.wait_element(self.browser, '//td[text()=" > File Parties"]')
        com.wait_element(self.browser, '//td[@width="15%"]/a')
        com.take_screenshot(self.browser, "check_parties_pacer_2")
        parties_on_caseaware = self.browser.find_elements('//td[@width="15%"]/a')
        for ca_party in parties_on_caseaware:
            for debtor in pacer_data['Debtor']:
                debtor_name_parts = debtor['name'].split(' ')
                if len(debtor_name_parts) > 2:
                    if debtor_name_parts[0].lower() in ca_party.text.lower() and debtor_name_parts[1].lower() in ca_party.text.lower() and debtor_name_parts[2].lower() in ca_party.text.lower():
                        debtor['status'] = 'to_validate'
                else:
                    if debtor_name_parts[0].lower() in ca_party.text.lower() and debtor_name_parts[1].lower() in ca_party.text.lower():
                        debtor['status'] = 'to_validate'
        for debtor in pacer_data['Debtor']:
            com.wait_element(self.browser, '//a[@class="tabs_href"]/font[text()="Parties"]')
            try:
                self.browser.click_element_when_visible('//a[@class="tabs_href"]/font[text()="Parties"]')
            except:
                pass
            if 'status' in debtor:
                if debtor['status'] == 'to_validate':
                    self.validate_party_pacer(debtor)
            else:
                if 'borrower' not in debtor:
                    self.add_party_pacer(debtor)
        com.log_message('Parties are valid from Pacer')

    def add_party_pacer(self, pacer_data: dict):
        # we're on Parties page. Click "New"
        self.browser.click_element_when_visible('//a[text()="New"]')
        com.wait_element(self.browser, '//select[@id="fdid"]')
        self.browser.select_from_list_by_value('//select[@id="fdid"]', '7')
        self.browser.input_text_when_element_is_visible('//input[@id="fname"]', pacer_data['parsed_first_name'])
        self.browser.input_text_when_element_is_visible('//input[@id="middle"]', pacer_data['parsed_middle_name'])
        self.browser.input_text_when_element_is_visible('//input[@id="lname"]', pacer_data['parsed_last_name'])
        self.browser.input_text_when_element_is_visible('//input[@id="addr1"]', pacer_data['address'])
        self.browser.input_text_when_element_is_visible('//input[@id="city"]', pacer_data['parsed_city'])
        self.browser.select_from_list_by_value('//select[@id="state"]', pacer_data['parsed_state'])
        self.browser.input_text_when_element_is_visible('//input[@id="zip"]', pacer_data['parsed_zip'])
        self.browser.set_focus_to_element('//select[@id="county_id"]')
        time.sleep(1)
        county_ca = self.browser.get_selected_list_label('//select[@id="county_id"]')
        com.log_message(county_ca, 'TRACE')
        if county_ca == '-- SELECT --' or county_ca.strip() == '':
            self.browser.select_from_list_by_label('//select[@id="county_id"]', pacer_data['parsed_county'].strip())
        else:
            com.log_message('Validation success')
            pacer_data['status'] = 'added'
        if self.test_run:
            self.browser.go_back()
            # self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
        else:
            self.browser.click_element_when_visible('//a[text()="Save"]')

    def validate_party_pacer(self, pacer_data: dict):
        com.log_message('Debtor on Pacer Docket in CaseAware Validation', 'TRACE')
        com.wait_element(self.browser, '//td[text()=" > File Parties"]')
        com.wait_element(self.browser, '//td[@width="15%"]/a', 15)
        com.take_screenshot(self.browser, "validate_party_pacer_1")
        is_need_to_save: bool = False
        # self.browser.select_from_list_by_value('//select[@id="fdid"]', str(7))
        need_to_handle_alert = False
        temp_lname = pacer_data["parsed_last_name"].lower()
        temp_fname = pacer_data["parsed_first_name"].lower()
        temp_mname = pacer_data["parsed_middle_name"].lower()
        com.log_message(f'Searching for {temp_fname} {temp_lname} {temp_mname}', 'TRACE')
        party = self.browser.find_elements(
            f'//td[@width="15%"]/a[{com.contains_lower_xpath(temp_lname)} and {com.contains_lower_xpath(temp_fname)} and {com.contains_lower_xpath(temp_mname)}]')
        if len(party) > 0:
            party[0].click()
        com.take_screenshot(self.browser, "validate_party_pacer_2")
        com.wait_element(self.browser, '//input[@id="fname"]')
        if self.browser.is_element_visible('//select[@id="fdid"]'):
            self.browser.select_from_list_by_value('//select[@id="fdid"]', str(7))
            is_need_to_save = True
            need_to_handle_alert = True
        fname_ca = self.browser.find_element('//input[@id="fname"]').get_attribute('value').lower()
        mname_ca = self.browser.find_element('//input[@id="middle"]').get_attribute('value').lower()
        lname_ca = self.browser.find_element('//input[@id="lname"]').get_attribute('value').lower()
        address_1_ca = self.browser.find_element('//input[@id="addr1"]').get_attribute('value').lower()
        city_ca = self.browser.find_element('//input[@id="city"]').get_attribute('value').lower()
        state_ca = self.browser.get_selected_list_label('//select[@id="state"]').lower()
        zip_ca = self.browser.find_element('//input[@id="zip"]').get_attribute('value').lower()
        if fname_ca not in pacer_data['parsed_first_name'].lower() or fname_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="fname"]', pacer_data['parsed_first_name'])
            is_need_to_save = True
        if mname_ca not in pacer_data['parsed_middle_name'].lower() or mname_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="middle"]', pacer_data['parsed_middle_name'])
            is_need_to_save = True
        if lname_ca not in pacer_data['parsed_last_name'].lower() or lname_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="lname"]', pacer_data['parsed_last_name'])
            is_need_to_save = True
        if address_1_ca.lower() not in pacer_data['address'].lower() or address_1_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="addr1"]', pacer_data['address'])
            is_need_to_save = True
        if city_ca not in pacer_data['parsed_city'].lower() or city_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="city"]', pacer_data['parsed_city'])
            is_need_to_save = True
        if state_ca not in pacer_data['parsed_state'].lower() or state_ca == '':
            self.browser.select_from_list_by_value('//select[@id="state"]', pacer_data['parsed_state'])
            is_need_to_save = True
        if not self.check_both_ways_value(zip_ca, pacer_data['parsed_zip'].lower()) or zip_ca == '':
            self.browser.input_text_when_element_is_visible('//input[@id="zip"]', pacer_data['parsed_zip'])
            is_need_to_save = True
        self.browser.set_focus_to_element('//select[@id="county_id"]')
        time.sleep(1)
        county_ca = self.browser.get_selected_list_label('//select[@id="county_id"]')
        com.log_message(county_ca, 'TRACE')
        if county_ca == '-- SELECT --' or county_ca.strip() == '':
            self.browser.select_from_list_by_label(pacer_data['parsed_county'])
            is_need_to_save = True
        else:
            com.log_message('Validation pacer success', 'TRACE')
            changed_fields = self.browser.find_elements('//input[@style="background-color: rgb(241, 249, 255);"]')
            if len(changed_fields) > 0:
                is_need_to_save = True
            else:
                is_need_to_save = False
            pacer_data['status'] = 'validated'
        if self.test_run or not is_need_to_save:
            self.browser.go_back()
            try:
                com.take_screenshot(self.browser, "validate_party_pacer_3")
                self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
            except:
                pass
        else:
            try:
                com.take_screenshot(self.browser, "validate_party_pacer_4")
                self.browser.click_element_when_visible('//a[text()="Save"]')
                self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
                com.take_screenshot(self.browser, "validate_party_pacer_5")
            except:
                pass
            if need_to_handle_alert:
                try:
                    self.browser.switch_window(self.browser.get_window_handles()[1])
                    self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
                    self.browser.switch_window(self.browser.get_window_handles()[0])
                    com.take_screenshot(self.browser, "validate_party_pacer_6")
                except:
                    self.browser.switch_window(self.browser.get_window_handles()[0])
                    self.browser.go_back()
                    try:
                        com.take_screenshot(self.browser, "validate_party_pacer_3")
                        self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
                    except:
                        pass

    def remove_prepopulated_bk_if_any(self):
        com.log_message('Removing prepopulated BK entities', 'TRACE')
        com.wait_element(self.browser, '//a/font[text()="Entities"]')
        self.browser.click_element_when_visible('//a/font[text()="Entities"]')
        com.wait_element(self.browser, '//td[contains(text(),"File Entities")]')
        elem_remove = self.browser.find_elements(
            '//td[contains(text(), "BK")]/following-sibling::td/a[contains(text(), "Remove")]')
        for elem in elem_remove:
            try:
                elem.click()
                self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
            except:
                pass

    def complete_mortgage_payment_change_form(self, doc_type, data):
        com.log_message('Opening mortgage_payment_change_form', 'TRACE')
        self.open_mort_pmt_chg()
        com.log_message('Processing mortgage_payment_change_form', 'TRACE')
        if doc_type == "EA":
            self.escrow_change_process(data)
        elif doc_type == "ARM":
            self.interest_change_process(data)
        com.log_message('Saving mortgage_payment_change_form', 'TRACE')
        if self.test_run:
            self.browser.highlight_elements(locator='//*[@id="save_new_del_top"]/a[contains(text(), "Save")]',
                                            style="solid", width="3px", color="orange")
            self.browser.go_back()
        else:
            try:
                self.browser.click_element_when_visible('//*[@id="save_new_del_top"]/a[contains(text(), "Save")]')
                self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
            except Exception as ex:
                com.log_message('Error in Mort Pmt Chg flow:', 'TRACE')
                com.log_message(str(ex), 'TRACE')
                traceback.print_exc()
                com.take_screenshot(self.browser, 'Mort Pmt Chg_exception')
                com.log_DOM(self.browser)
                self.browser.go_back()

    def escrow_change_process(self, escrow_data):
        self.browser.input_text_when_element_is_visible('//input[@id="udf_10"]',
                                                        datetime.strptime(escrow_data['due date'],
                                                                          "%m/%d/%y").strftime("%m/%d/%Y"))
        if escrow_data['shortage_pymt_curr'] == '0':
            curr_insert_sum = str(decimal.Decimal(escrow_data['current escrow payment']) + decimal.Decimal(
                escrow_data['surplus_pymt_curr']))
        else:
            curr_insert_sum = str(decimal.Decimal(escrow_data['current escrow payment']) + decimal.Decimal(
                escrow_data['shortage_pymt_curr']))
        if escrow_data['shortage_pymt_new'] == '0':
            new_insert_sum = str(
                decimal.Decimal(escrow_data['new escrow payment']) + decimal.Decimal(escrow_data['surplus_pymt_new']))
        else:
            new_insert_sum = str(
                decimal.Decimal(escrow_data['new escrow payment']) + decimal.Decimal(escrow_data['shortage_pymt_new']))
        self.browser.input_text_when_element_is_visible('//input[@id="udf_50"]', curr_insert_sum)
        self.browser.input_text_when_element_is_visible('//input[@id="udf_100"]', new_insert_sum)
        self.browser.input_text_when_element_is_visible('//input[@id="udf_110"]', escrow_data['new total payment'])

    def interest_change_process(self, arm_change_data):
        self.browser.input_text_when_element_is_visible('//input[@id="udf_10"]',
                                                        datetime.strptime(arm_change_data['due date'],
                                                                          "%m/%d/%y").strftime("%m/%d/%Y"))
        self.browser.input_text_when_element_is_visible('//input[@id="udf_30"]',
                                                        arm_change_data['current interest rate'])
        current_principal_and_interest: decimal.Decimal = decimal.Decimal(arm_change_data['current principal']) + decimal.Decimal(arm_change_data['current interest'])
        self.browser.input_text_when_element_is_visible('//input[@id="udf_40"]', str(current_principal_and_interest))
        self.browser.input_text_when_element_is_visible('//input[@id="udf_80"]', arm_change_data['new interest rate'])
        new_principal_and_interest: decimal.Decimal = decimal.Decimal(arm_change_data['new principal']) + decimal.Decimal(arm_change_data['new interest'])
        self.browser.input_text_when_element_is_visible('//input[@id="udf_90"]', str(new_principal_and_interest))
        self.browser.input_text_when_element_is_visible('//input[@id="udf_110"]', arm_change_data['new total'])

    def open_mort_pmt_chg(self):
        try:
            self.browser.click_element_when_visible('//a[@id="#tabs_row_1_link"]')
            com.wait_element(self.browser, '//ul[@id="#tabs_row_1_ul"]/li/a/font[contains(text(), "Mort Pmt Chg")]')
            self.browser.click_element_when_visible(
                '//ul[@id="#tabs_row_1_ul"]/li/a/font[contains(text(), "Mort Pmt Chg")]')
            com.wait_element(self.browser, "//div[@class='page-title' and contains(text(), 'Mortgage Payment Change')]")
        except Exception as ex:
            raise Exception("Unable to open 'Mort Pmt Chg'. " + str(ex))

    def case_sendout_generate_nopc(self, debtor_1, debtor_2=None):
        if debtor_2 is None:
            debtor_2_fname = ''
            debtor_2_lname = ''
        else:
            debtor_2_parts = debtor_2["name"].lower().split(' ')
            debtor_2_fname = debtor_2_parts[0].strip()
            debtor_2_lname = debtor_2_parts[len(debtor_2_parts) - 1].strip()
        debtor_1_parts = debtor_1["name"].lower().split(' ')
        debtor_1_fname = debtor_1_parts[0].strip()
        debtor_1_lname = debtor_1_parts[len(debtor_1_parts) - 1].strip()

        locator_template_checkbox = '//td[@align="left"]//tr[{}]//tr/td[{} and {}]/preceding-sibling::td/input[@type="checkbox"]'

        try:
            com.wait_element(self.browser, '//a/font[text()="Case Sendout"]')
            self.browser.click_element_when_visible('//a/font[text()="Case Sendout"]')
            self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
        except:
            try:
                self.browser.click_element_when_visible('//*[@id="save_new_del_top"]/a[contains(text(), "Save")]')
                self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
            except:
                self.browser.go_back()
            com.wait_element(self.browser, '//a/font[text()="Case Sendout"]')
            self.browser.click_element_when_visible('//a/font[text()="Case Sendout"]')
        # self.browser.click_element_when_visible(
        #     '//td[text()="bk_Notice of Payment Change"]/preceding-sibling::td[input[@type="checkbox"]]')
        # New requirements
        self.browser.click_element_when_visible(
            '//td[text()="bk_Notice of Payment Change CMSBK"]/preceding-sibling::td[input[@type="checkbox"]]')

        self.browser.click_element_when_visible('//tbody//tr//td//a[@class="button" and contains(text(), "Generate")]')
        com.wait_element(self.browser, '//tr/td/b[text()="Requirements"]')

        checkboxes = self.browser.find_elements('//table/tbody/tr/td/input[@type="checkbox"]')
        is_two_borrowers = len(checkboxes) == 6

        if is_two_borrowers:
            # section_1
            self.browser.select_checkbox(locator_template_checkbox.format("1", com.contains_lower_xpath(debtor_1_fname),
                                                                          com.contains_lower_xpath(debtor_1_lname)))
            self.browser.unselect_checkbox(
                locator_template_checkbox.format("1", com.contains_lower_xpath(debtor_2_fname),
                                                 com.contains_lower_xpath(debtor_2_lname)))

            # section_2
            self.browser.unselect_checkbox(
                locator_template_checkbox.format("2", com.contains_lower_xpath(debtor_1_fname),
                                                 com.contains_lower_xpath(debtor_1_lname)))
            self.browser.select_checkbox(locator_template_checkbox.format("2", com.contains_lower_xpath(debtor_2_fname),
                                                                          com.contains_lower_xpath(debtor_2_lname)))

            # section_3
            self.browser.select_checkbox(locator_template_checkbox.format("3", com.contains_lower_xpath(debtor_1_fname),
                                                                          com.contains_lower_xpath(debtor_1_lname)))
            self.browser.unselect_checkbox(
                locator_template_checkbox.format("3", com.contains_lower_xpath(debtor_2_fname),
                                                 com.contains_lower_xpath(debtor_2_lname)))

            self.browser.click_element_when_visible('//a[text()="Continue"]')
            com.wait_element(self.browser,
                             "//table/tbody/tr[td/b[text() ='Parties Text, Block 2']]/following-sibling::tr/td/textarea")

        else:
            for checkbox_item in checkboxes:
                if not checkbox_item.is_selected():
                    checkbox_item.click()

            self.browser.click_element_when_visible('//a[text()="Continue"]')
            com.wait_element(self.browser,
                             "//table/tbody/tr[td/b[text() ='Parties Text, Block 2']]/following-sibling::tr/td/textarea")
            self.browser.clear_element_text(
                "//table/tbody/tr[td/b[text() ='Parties Text, Block 2']]/following-sibling::tr/td/textarea")

        self.browser.click_element_when_visible('//a[text()="Continue"]')
        com.wait_element(self.browser, '//a[contains(text(),".doc")]')
        com.log_message('NOPC Successfully Generated')
        return self.get_and_check_is_file_download('.doc')

    def get_and_check_is_file_download(self, file_part_name) -> str:
        time.sleep(5)
        i = 0
        while i < 3:
            self.browser.click_element_when_visible('//a[contains(text(),".doc")]')
            counter = 0
            while counter < 500:
                try:
                    list_of_files = glob.glob(self.path_to_temp + '\*')
                    latest_file = max(list_of_files, key=os.path.getctime)
                    if file_part_name in latest_file:
                        return latest_file
                    counter += 1
                    time.sleep(1)
                except:
                    pass
            i += 1

    def create_bk_certificate_of_service_nopc(self):
        self.browser.click_element_when_visible('//a/font[text()="Case Sendout"]')
        # self.browser.click_element_when_visible(
        #     '//td[text()="bk_Certificate_of_Service_NOPC"]/preceding-sibling::td[input[@type="checkbox"]]')
        # New requirement
        self.browser.click_element_when_visible('//td[text()="bk_Certificate of Service NOPC CMSBK"]/preceding-sibling::td[input[@type="checkbox"]]')
        self.browser.click_element_when_visible('//tbody//tr//td//a[@class="button" and contains(text(), "Generate")]')
        com.wait_element(self.browser, '//tr/td/b[text()="Requirements"]')

        checkboxes = self.browser.find_elements('//table/tbody/tr/td/input[@type="checkbox"]')
        for checkbox_item in checkboxes:
            if not checkbox_item.is_selected():
                checkbox_item.click()

        self.browser.click_element_when_visible('//a[text()="Continue"]')
        com.wait_element(self.browser, "//table/tbody/tr[td/b[text() ='Parties Text, Block 2']]/following-sibling::tr/td/textarea")

        # block 1
        block_1: str = self.browser.get_text("//table/tbody/tr[td/b[text() ='Parties Text, Block 1']]/following-sibling::tr/td/textarea")
        names = list()
        for name_item in block_1.split(","):
            if not name_item.strip():
                continue
            names.append(name_item.strip())
        self.browser.clear_element_text("//table/tbody/tr[td/b[text() ='Parties Text, Block 1']]/following-sibling::tr/td/textarea")
        self.browser.input_text_when_element_is_visible("//table/tbody/tr[td/b[text() ='Parties Text, Block 1']]/following-sibling::tr/td/textarea", "\n".join(names))

        # block 2
        block_2: str = self.browser.get_text("//table/tbody/tr[td/b[text() ='Parties Text, Block 2']]/following-sibling::tr/td/textarea")
        block_2_lines = block_2.split("\n")
        # get addresses
        addresses = list()
        for line_item in block_2_lines:
            str_value = line_item.strip()
            for name_item in names:
                if line_item.find(name_item) != -1:
                    str_value: str = line_item.replace(name_item, "").strip()
            if not str_value.strip():
                continue
            addresses.append(str_value)
        # remove duplicates
        addresses = list(dict.fromkeys(addresses))
        new_content = "\n".join(names) + "\n" + "\n".join(addresses)
        self.browser.clear_element_text("//table/tbody/tr[td/b[text() ='Parties Text, Block 2']]/following-sibling::tr/td/textarea")
        self.browser.input_text_when_element_is_visible("//table/tbody/tr[td/b[text() ='Parties Text, Block 2']]/following-sibling::tr/td/textarea", new_content)

        # block 3
        self.browser.clear_element_text("//table/tbody/tr[td/b[text() ='Parties Text, Block 3']]/following-sibling::tr/td/textarea")

        self.browser.click_element_when_visible('//a[text()="Continue"]')
        com.wait_element(self.browser, '//a[contains(text(),".doc")]')
        com.log_message('COS file generated')

    def navigate_to_case(self, case_number: str):
        try:
            self.browser.go_to(f'{self.base_url}/index.php')
            com.wait_element(self.browser, '//input[@name="filt_cnum" and @type="text"]')
            self.browser.input_text_when_element_is_visible('//input[@name="filt_cnum" and @type="text"]', case_number)
            com.wait_element(self.browser, '//a[@class="button" and text()="Find Case"]')
            self.browser.click_element_when_visible('//a[@class="button" and text()="Find Case"]')
            com.wait_element(self.browser, '//a[contains(., "View Case")]')
        except Exception as ex:
            com.log_message('Error in navigate_to_case flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'navigate_to_case_exception')
            com.log_DOM(self.browser)

    def navigate_to_home(self):
        bot_not_at_home: bool = True
        timer: datetime = datetime.now() + timedelta(0, 60 * 2)

        while bot_not_at_home and timer > datetime.now():
            try:
                self.browser.go_to(f'{self.base_url}/index.php')
                com.wait_element(self.browser, '//input[@name="filt_cnum" and @type="text"]')
                bot_not_at_home = not self.browser.is_element_visible('//input[@name="filt_cnum" and @type="text"]')
            except:
                pass

    def email_exception_old(self, case: str, loan_number: str):
        com.log_message('Exceptions Email Validation')
        app = Application()
        app.open_application()

        recepient = 'direct@ta.com'
        # mail_obj = MailMessage(bot_identity=self.bot_creds['login'], bot_credentials=self.bot_creds)
        subject = 'Loan {loan_number} unidentifiable {exception}'
        body = """Hello!\nTA is unable to process Case {loan_number} because the {exception} is unidentifiable. A human needs to resolve this issue and complete the NOPC generation steps. The bot can pick up at e-filing once task 2390 comes due.\nPlease reach out to your customer success manager if you have any questions, we're here to help!"""
        if case == 'county':
            app.send_message(
                subject=subject.format(loan_number=loan_number, exception='Borrower Zip Code'),
                body=body.format(loan_number=loan_number, exception='Borrower Zip Code'),
                recipients=recepient
            )
        elif case == 'court':
            app.send_message(
                subject=subject.format(loan_number=loan_number, exception='Court'),
                body=body.format(loan_number=loan_number, exception='Court'),
                recipients=recepient
            )
        elif case == 'judge':
            app.send_message(
                subject=subject.format(loan_number=loan_number, exception='Judge'),
                body=body.format(loan_number=loan_number, exception='Judge'),
                recipients=recepient
            )
        elif case == 'trustee':
            app.send_message(
                subject=subject.format(loan_number=loan_number, exception='Trustee'),
                body=body.format(loan_number=loan_number, exception='Trustee'),
                recipients=recepient
            )
        elif case == 'debtor_attorney':
            app.send_message(
                subject=subject.format(loan_number=loan_number, exception='Debtor Attorney'),
                body=body.format(loan_number=loan_number, exception='Debtor Attorney'),
                recipients=recepient
            )
        elif case == 'us_trustee':
            app.send_message(
                subject=subject.format(loan_number=loan_number, exception='US Trustee'),
                body=body.format(loan_number=loan_number, exception='US Trustee'),
                recipients=recepient
            )

    def email_exception(self, case: str, loan_number: str):
        com.log_message('Exceptions Email Validation')

        recepient = 'direct@ta.com'
        mail_obj = MailMessage(bot_identity=self.bot_creds['login'], bot_credentials=self.bot_creds)
        subject = 'Loan {loan_number} unidentifiable {exception}'
        body = """Hello!\nTA is unable to process Case {loan_number} because the {exception} is unidentifiable. A human needs to resolve this issue and complete the NOPC generation steps. The bot can pick up at e-filing once task 2390 comes due.\nPlease reach out to your customer success manager if you have any questions, we're here to help!"""
        if case == 'county':
            mail_obj.send_message(
                subject.format(loan_number=loan_number, exception='Borrower Zip Code'),
                body.format(loan_number=loan_number, exception='Borrower Zip Code'),
                recepient
            )
        elif case == 'court':
            mail_obj.send_message(
                subject.format(loan_number=loan_number, exception='Court'),
                body.format(loan_number=loan_number, exception='Court'),
                recepient
            )
        elif case == 'judge':
            mail_obj.send_message(
                subject.format(loan_number=loan_number, exception='Judge'),
                body.format(loan_number=loan_number, exception='Judge'),
                recepient
            )
        elif case == 'trustee':
            mail_obj.send_message(
                subject.format(loan_number=loan_number, exception='Trustee'),
                body.format(loan_number=loan_number, exception='Trustee'),
                recepient
            )
        elif case == 'debtor_attorney':
            mail_obj.send_message(
                subject.format(loan_number=loan_number, exception='Debtor Attorney'),
                body.format(loan_number=loan_number, exception='Debtor Attorney'),
                recepient
            )
        elif case == 'us_trustee':
            mail_obj.send_message(
                subject.format(loan_number=loan_number, exception='US Trustee'),
                body.format(loan_number=loan_number, exception='US Trustee'),
                recepient
            )

    def validate_file_content(self, loan_data):
        com.log_message('Validating existing file in CaseAware')
        com.take_screenshot(self.browser, 'validating file content')
        is_need_to_save = False
        com.wait_element(self.browser, '//a/font[contains(text(), "Edit File")]')
        self.browser.click_element_when_visible('//a/font[contains(text(), "Edit File")]')
        com.wait_element(self.browser, '//select[@name="site_id"]')
        ca_site_id = self.browser.get_selected_list_label('//select[@name="site_id"]').lower().strip()
        ca_beneficiary = self.browser.find_element('//input[@id="disp_ben_id"]').get_attribute('value').lower().strip()
        ca_loan_type = self.browser.get_selected_list_label('//select[@name="loan_type_id"]').lower().strip()
        ca_loan_num = self.browser.find_element('//input[@name="loan_num"]').get_attribute('value').lower().strip()
        ca_addr_1 = self.browser.find_element('//input[@name="prop_addr1"]').get_attribute('value').lower().strip()
        ca_addr_2 = self.browser.find_element('//input[@name="prop_addr2"]').get_attribute('value').lower().strip()
        ca_addr_3 = self.browser.find_element('//input[@name="prop_addr3"]').get_attribute('value').lower().strip()
        ca_city = self.browser.find_element('//input[@name="city"]').get_attribute('value').lower().strip()
        ca_state = self.browser.find_element('//select[@name="state"]').get_attribute('value').lower().strip()
        ca_zip = self.browser.find_element('//input[@name="zip"]').get_attribute('value').lower().strip()
        ca_dwel_type = self.browser.get_selected_list_label('//select[@name="dwell_type_id"]').lower().strip()
        ca_county = self.browser.get_selected_list_label('//select[@id="county_id"]').lower().strip()

        if ca_site_id == '':
            com.wait_element(self.browser, '//select[@name="site_id"]')
            self.browser.select_from_list_by_value('//select[@name="site_id"]',
                                                   self.REF_SITE_MAPPING[loan_data['referral_site']])
            self.browser.click_element_when_visible('//a[text()="Pick Client"]')
            browser_tabs = self.browser.get_window_handles()
            self.browser.switch_window(browser_tabs[1])
            self.browser.click_element_when_visible('//option[contains(text(),"Carrington Mortgage Services, LLC")]')
            self.browser.click_element_when_visible('//a[text()="Save"]')
            self.browser.switch_window(self.browser.get_window_handles()[0])
            self.browser.select_from_list_by_value('//select[@name="client_cd_id"]', str(433))
            is_need_to_save = True
            com.log_message('ca_site_id edited')

        if ca_beneficiary == '':
            self.browser.click_element_when_visible('//a[text()="Choose Beneficiary"]')
            time.sleep(1)
            browser_tabs = self.browser.get_window_handles()
            self.browser.switch_window(browser_tabs[1])
            self.browser.input_text_when_element_is_visible('//input[@name="filt_nm"]',
                                                            loan_data['vest_in_the_name_of'])
            self.browser.click_element_when_visible('//a[text()="Filter"]')
            self.browser.click_element_when_visible('//option')
            self.browser.click_element_when_visible('//a[text()="Save"]')
            browser_tabs = self.browser.get_window_handles()
            self.browser.switch_window(browser_tabs[0])
            is_need_to_save = True
            com.log_message('ca_beneficiary edited')

        # Beneficiary - copy details from Tempo field Vest in the Name of and in CaseAware select choose beneficiary and paste the details into the Name search box and hit enter to search. Is the bank returned?
        # Yes - select it by double clicking
        # No - select New and paste the details into the Corp. Name field and Save (No new button)
        # TODO add new beneficiary flow:
        # click '//a[text() = "New"]'
        # switch window to pop-up
        # wait element '//textarea[@id="co_name"]'
        # input text to '//textarea[@id="co_name"]'
        # click save '//a[text()="Save"]'
        if ca_loan_type == '':
            self.browser.select_from_list_by_value('//select[@name="loan_type_id"]',
                                                   CaseAware.LOAN_TYPE_MAPPING[loan_data['loan_type']])
            is_need_to_save = True
            com.log_message('ca_loan_type edited')
        if ca_loan_num == '':
            self.browser.input_text_when_element_is_visible('//input[@name="loan_num"]', loan_data['loan_number'])
            is_need_to_save = True
            com.log_message('ca_loan_num edited')
        if ca_addr_1 == '' and loan_data['property_address_1'] != '':
            self.browser.input_text_when_element_is_visible('//input[@name="prop_addr1"]',
                                                            loan_data['property_address_1'])
            is_need_to_save = True
            com.log_message('ca_addr_1 edited')
        if ca_addr_2 == '' and loan_data['property_address_2'] != '':
            self.browser.input_text_when_element_is_visible('//input[@name="prop_addr2"]',
                                                            loan_data['property_address_2'])
            is_need_to_save = True
            com.log_message('ca_addr_2 edited')
        if ca_addr_3 == '' and loan_data['property_address_3'] != '':
            self.browser.input_text_when_element_is_visible('//input[@name="prop_addr3"]',
                                                            loan_data['property_address_3'])
            is_need_to_save = True
            com.log_message('ca_addr_3 edited')
        if ca_city == '':
            self.browser.input_text_when_element_is_visible('//input[@name="city"]', loan_data['city'])
            is_need_to_save = True
            com.log_message('ca_city edited')
        if ca_state == '':
            self.browser.select_from_list_by_value('//select[@name="state"]', loan_data['state'])
            is_need_to_save = True
            com.log_message('ca_state edited')
        if ca_zip == '':
            self.browser.input_text_when_element_is_visible('//input[@name="zip"]', loan_data['zip_code'])
            is_need_to_save = True
            com.log_message('ca_zip edited')
        if ca_dwel_type == '':
            self.browser.select_from_list_by_value('//select[@name="dwell_type_id"]', str(1))
            is_need_to_save = True
            com.log_message('ca_dwel_type edited')
        if ca_county == '' or ca_county == '-- select --':
            com.wait_element(self.browser, '//select[@id="county_id"]')
            county_ca = self.browser.get_selected_list_label('//select[@id="county_id"]')
            com.log_message(county_ca)
            time.sleep(5)
            if county_ca == '-- SELECT --' or county_ca.strip() == '':
                if loan_data['county'] != '':
                    # populate from tempo if available
                    self.browser.select_from_list_by_label('//select[@id="county_id"]', loan_data['county'].strip())
                elif loan_data['pacer_data']['Debtor'][0]['parsed_county'].strip() != '':
                    # populate county from pacer
                    temp_county = loan_data['pacer_data']['Debtor'][0]['parsed_county'].strip()
                    self.browser.select_from_list_by_label('//select[@id="county_id"]', temp_county)
                else:
                    self.email_exception('county', loan_data['loan_number'])
                    return
            is_need_to_save = True
            com.log_message('ca_county edited')
        if self.test_run or not is_need_to_save:
            self.browser.go_back()
            self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
        else:
            self.browser.click_element_when_visible('//div[@id="save_new_del_top"]/a[text()="Save"]')
            self.browser.alert_should_not_be_present(timeout=timedelta(0, 60))
            i = 0
            while i < 100:
                try:
                    self.browser.switch_window(self.browser.get_window_handles()[1])
                    com.wait_element(self.browser, '//a[text()="Save"]')
                    self.browser.click_element_when_visible('//a[text()="Save"]')
                    self.browser.switch_window(self.browser.get_window_handles()[0])
                    break
                except:
                    pass
                time.sleep(1)
                i += 1

    def check_both_ways_value(self, value1, value2):
        if value1 in value2:
            return True
        elif value2 in value1:
            return True
        else:
            return False

    def compare_and_label_parties(self, loan_data):
        def compare_names_addresses(p_t, p_p) -> bool:
            flag_fn = p_t['first_name'].lower().strip() == p_p['parsed_first_name'].lower().strip()
            flag_mn = p_t['middle_name'].lower().strip() == p_p['parsed_middle_name'].lower().strip()
            flag_ln = p_t['last_name'].lower().strip() == p_p['parsed_last_name'].lower().strip()
            flag_addr = p_t['address_1'].lower().strip() == p_p['address'].lower().strip()
            if flag_fn and flag_mn and flag_ln and flag_addr:
                return True
            else:
                return False

        tempo_parties = loan_data['parties']
        pacer_parties = loan_data['pacer_data']['Debtor']
        for t_party in tempo_parties:
            for p_party in pacer_parties:
                if 'borrower' not in p_party:
                    if compare_names_addresses(t_party, p_party):
                        t_party['debtor'] = True
                        p_party['borrower'] = True

    def validate_datty_address(self, name_parts, other):
        # locate Edit button
        search_term = ''
        for np in name_parts:
            if search_term == '':
                search_term = com.contains_lower_xpath(np, '.')
            else:
                search_term = search_term + ' and ' + com.contains_lower_xpath(np, '.')
        com.wait_element(self.browser, f'//tr/td[a[{search_term}]]/following-sibling::td/a[text()="Edit"]')
        if self.browser.does_page_contain_element(f'//tr/td[a[{search_term}]]/following-sibling::td/a[text()="Edit"]'):
            self.browser.click_element_when_visible(f'//tr/td[a[{search_term}]]/following-sibling::td/a[text()="Edit"]')
        else:
            com.log_message('No edit button on entity', 'TRACE')
            return
        com.wait_element(self.browser, '//input[@id="addr1"]')
        curr_addr = self.browser.find_element('//input[@id="addr1"]').get_attribute('value')
        addr_rows = []
        addr_row_flag = False
        city_parsed = ''
        state_parsed = ''
        zip_parsed = ''
        for opart in other:
            x = re.search("^\d+", opart)
            y = re.search('^\D+\,\s*[A-Z]{2}\s*\d+', opart)
            if y:
                com.log_message("City-state-zip row reached:", 'TRACE')
                com.log_message(opart, 'TRACE')
                com.log_message("Address looks like:", 'TRACE')
                com.log_message(' '.join(addr_rows), 'TRACE')
                try:
                    city_parsed = opart.split(',')[0].strip()
                    state_parsed = opart.split(',')[1].strip().split(' ')[0].strip()
                    zip_parsed = opart.split(',')[1].strip().split(' ')[1].strip()
                except:
                    com.log_message('Failed to parse city state or zip from pacer debtor attorney', 'TRACE')
                break
            if x or addr_row_flag:
                com.log_message("Possible address row:", 'TRACE')
                com.log_message(opart, 'TRACE')
                addr_rows.append(str(opart).strip())
                addr_row_flag = True
            else:
                com.log_message("Not an address row:", 'TRACE')
                com.log_message(opart, 'TRACE')
        address_correct = ' '.join(addr_rows)
        if curr_addr in address_correct:
            self.browser.go_back()
            return
        self.browser.input_text_when_element_is_visible('//input[@id="addr1"]', address_correct)
        self.browser.input_text_when_element_is_visible('//input[@id="addr2"]', '')
        self.browser.input_text_when_element_is_visible('//input[@id="addr3"]', '')
        self.browser.input_text_when_element_is_visible('//input[@id="city"]', city_parsed)
        self.browser.select_from_list_by_value('//select[@id="state"]', state_parsed)
        self.browser.input_text_when_element_is_visible('//input[@id="zip"]', zip_parsed)
        lbl_list = self.browser.get_list_items('//select[@id="county_id"]')
        if len(lbl_list) > 1:
            self.browser.select_from_list_by_index('//select[@id="county_id"]', '1')
        time.sleep(1)
        self.browser.click_element_when_visible('//div[@id="save_new_del_top"]/a[text()="Save"]')
        try:
            time.sleep(1)
            self.browser.switch_window(self.browser.get_window_handles()[1])
            time.sleep(1)
            self.browser.click_element_when_visible('//a[text()="Save"]')
        except Exception as e:
            com.log_message('Unexpected window appeared and closed: ' + str(e), 'TRACE')
            time.sleep(1)
            try:
                time.sleep(1)
                self.browser.switch_window(self.browser.get_window_handles()[1])
                time.sleep(1)
                self.browser.click_element_when_visible('//a[text()="Save"]')
            except Exception as e:
                com.log_message('Unexpected window appeared and closed: ' + str(e), 'TRACE')
                time.sleep(1)
        try:
            self.browser.alert_should_not_be_present()
        except:
            com.log_message('There was a problem with alert', 'TRACE')
        time.sleep(5)

    def get_correct_address(self, initial_arr):
        ret_dict = {}
        addr_rows = []
        addr_row_flag = False
        city_parsed = ''
        state_parsed = ''
        zip_parsed = ''
        for opart in initial_arr:
            x = re.search("^\d+", opart)
            y = re.search('^\D+\,\s*[A-Z]{2}\s*\d+', opart)
            if y:
                com.log_message("City-state-zip row reached:", 'TRACE')
                com.log_message(opart, 'TRACE')
                com.log_message("Address looks like:", 'TRACE')
                com.log_message(' '.join(addr_rows), 'TRACE')
                try:
                    city_parsed = opart.split(',')[0].strip()
                    state_parsed = opart.split(',')[1].strip().split(' ')[0].strip()
                    zip_parsed = opart.split(',')[1].strip().split(' ')[1].strip()
                except:
                    com.log_message('Failed to parse city state or zip from pacer debtor attorney', 'TRACE')
                break
            if x or addr_row_flag:
                com.log_message("Possible address row:", 'TRACE')
                com.log_message(opart, 'TRACE')
                addr_rows.append(str(opart).strip())
                addr_row_flag = True
            else:
                com.log_message("Not an address row:", 'TRACE')
                com.log_message(opart, 'TRACE')
        ret_dict['addr'] = ' '.join(addr_rows)
        ret_dict['city'] = city_parsed
        ret_dict['state'] = state_parsed
        ret_dict['zip'] = zip_parsed
        return ret_dict
