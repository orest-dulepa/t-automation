import glob
import os
import re
import time
import traceback
from datetime import datetime, timedelta
from RPA.Browser.Selenium import Selenium
from RPA.PDF import PDF
from selenium.webdriver.common.keys import Keys
from libraries import common as com
from libraries.ocr_pdf import OcrPdf
from libraries.parse_pdf_docs import ParsePDFDOcs
import fitz


def get_sensitive_data(lines, loan_number):
    code_replace_pattern = r'(\d{4}-\d{2}-\d{2}-\d{7}-\d{4}-\d{7})'
    code_in_text_replace_pattern = r'(.*\*\*AUTO.*)'
    eqaliser_code_replace_pattern = r'([FTAD]{65})'
    square_barcode_replace_pattern = r'([01]{20})'
    for line in lines:
        # matching the regex to each line
        if re.search(rf'({loan_number})', line, re.IGNORECASE):
            search = re.search(rf'({loan_number})', line, re.IGNORECASE)
            yield search.group(1)
        if re.search(r'\*MODS\*', line, re.IGNORECASE):
            search = re.search(r'(\*MODS\*)', line, re.IGNORECASE)
            yield search.group(1)
        if re.search(code_replace_pattern, line, re.IGNORECASE):
            search = re.search(code_replace_pattern, line, re.IGNORECASE)
            yield search.group(1)
        if re.search(code_in_text_replace_pattern, line, re.IGNORECASE):
            search = re.search(code_in_text_replace_pattern, line, re.IGNORECASE)
            yield search.group(1)
        if re.search(eqaliser_code_replace_pattern, line, re.IGNORECASE):
            search = re.search(eqaliser_code_replace_pattern, line, re.IGNORECASE)
            yield search.group(1)
        if re.search(square_barcode_replace_pattern, line, re.IGNORECASE):
            search = re.search(square_barcode_replace_pattern, line, re.IGNORECASE)
            yield search.group(1)


STATE_DISTRICT_MAPPING = {
    'MI': 'michigan',
    'WI': 'wisconsin',
    'CO': 'colorado',
    'IL': 'illinois',
    'MN': 'minnesota',
    'WY': 'wyoming'
}


class Tempo:
    # TODO: optimise data scraping by placing all xpathes here, than iterate through them
    LOAN_DATA = {
        'a': 'a'
    }

    def __init__(self, credentials: dict, is_test_run: bool = False):
        self.test_run: bool = is_test_run
        self.is_failed: bool = False
        self.error_message: str = ''
        self.browser: Selenium = Selenium()
        self.credentials: dict = credentials
        self.is_site_available: bool = False
        self.loans = []
        root_path = os.environ.get("ROBOT_ROOT", os.getcwd())
        self.path_to_temp = os.path.join(root_path, 'temp')

    def open_login(self):
        self.browser.close_all_browsers()
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
                self.browser.maximize_browser_window()
                if not self.browser.does_page_contain_element("//input[@id='txtLoginName']"):
                    if not self.browser.find_element("//input[@id='txtLoginName']").is_displayed():
                        com.log_message("Logging into Tempo failed. Input field not found.", 'ERROR')
                        self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'Tempo_login_fail_{}.png'.format(count)))
                        return
                self.browser.input_text_when_element_is_visible("//input[@id='txtLoginName']", self.credentials['login'])
                self.browser.input_text_when_element_is_visible("//input[@id='txtPassword']", self.credentials['password'])
                self.browser.input_text_when_element_is_visible("//input[@id='txtAccountName']", self.credentials['Account'])
                self.browser.click_element_when_visible("//input[@class='loginbtn']")
                if self.browser.does_page_contain_element("//span[@id='lblErrMsg']"):
                    elem = self.browser.find_element("//span[@id='lblErrMsg']")
                    if elem.is_displayed() and not elem.text == "":
                        com.log_message("Logging into Tempo failed. {}".format(elem.text), 'ERROR')
                        raise Exception("Logging into Tempo failed. {}".format(elem.text), 'ERROR')
                if self.browser.is_element_visible('//input[@id="ctl00_ContentPlaceholderMain_btnVCClose"]'):
                    self.browser.click_element_when_visible('//input[@id="ctl00_ContentPlaceholderMain_btnVCClose"]')
                self.is_site_available = self.browser.does_page_contain_element("//a[@id='ctl00_hlnkWorklistQueue']")
                com.log_message('Bot successfully loged into Tempo')
            except Exception as ex:
                com.log_message("Logging into Tempo. Attempt #{} failed".format(count), 'ERROR')
                print(str(ex))
                self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'Tempo_login_fail_{}.png'.format(count)))
                self.browser.close_browser()
            finally:
                count += 1

    def check_1447_task_completed(self) -> bool:
        com.wait_element(self.browser, '//tr[td[contains(@id, "Bankruptcy")] and td/span[@class="greenfont"]]/following-sibling::tr//a[contains(text(), "Tasks")]')
        self.browser.click_element_when_visible('//tr[td[contains(@id, "Bankruptcy")] and td/span[@class="greenfont"]]/following-sibling::tr//a[contains(text(), "Tasks")]')
        com.wait_element(self.browser, '//span[text()="Bankruptcy - Tasks"]')
        proj_date_elements = self.browser.find_elements('//td[span[contains(text(), "Escrow Analysis/Pmt Change uploaded")]]/following-sibling::td[table/tbody/tr/td/span[contains(@id, "lblProjDate")]]')
        close_date_elements = self.browser.find_elements('//td[span[contains(text(), "Escrow Analysis/Pmt Change uploaded")]]/following-sibling::td[table/tbody/tr/td/span[contains(@id, "lblCloseDate")]]')
        for elem in close_date_elements:
            is_proj_date_displayed = proj_date_elements[close_date_elements.index(elem)].is_displayed()
            is_close_date_displayed = close_date_elements[close_date_elements.index(elem)].is_displayed()
            if is_proj_date_displayed and is_close_date_displayed:
                proj_date_text = proj_date_elements[close_date_elements.index(elem)].text
                close_date_text = close_date_elements[close_date_elements.index(elem)].text
                if proj_date_text != '' and close_date_text == '':
                    print('No close date for task 1447 in Tempo.')
                    return False
                else:
                    return True

    def get_worklist_queue(self, predefined_test_loan: str = '', predefined_file_type: str = ''):
        self.browser.click_element_when_visible("//td[contains(text(), 'Queue Management')]")
        self.browser.click_element_when_visible("//a[@id='ctl00_hlnkWorklistQueue']")
        if self.browser.does_page_contain_element("//input[@id='ctl00_ContentPlaceholderMain_btnFilter']"):
            self.browser.click_element_when_visible("//input[@id='ctl00_ContentPlaceholderMain_btnFilter']")
            self.browser.wait_until_element_is_not_visible('//img[@id="ctl00_ContentPlaceholderMain_imgWait"]', timedelta(0, 60))
            com.wait_element(self.browser, "//tr[@id='ctl00_ContentPlaceholderMain_trAssignment']")
            is_any_green = False
            grid_rows_xpath = '//tr[@class="gridrow" or @class="gridaltrow"]'
            days_due_col_xpath = '//td[@class="rbordergrid"]/span'
            loan_number_col_xpath = '//td[contains(@class,"rbordergrid")]/a[contains(@id,"lblLoanNumber")]'
            next_page_xpath = '//input[@id="ctl00_ContentPlaceholderMain_Nextbutton"]'
            self.loans = []
            while 1:
                grid_rows = self.browser.find_elements(grid_rows_xpath)
                days_due_col = self.browser.find_elements(days_due_col_xpath)
                loan_number_col = self.browser.find_elements(loan_number_col_xpath)
                if len(grid_rows) > 0:
                    count = 0
                    while count < len(grid_rows):
                        try:
                            if 'color: green;' in days_due_col[count].get_attribute('style').lower():
                                pending_loan_num = loan_number_col[count].get_attribute('innerText').strip()
                                print('Color is green for ' + pending_loan_num)
                                if predefined_test_loan != '':
                                    if pending_loan_num not in predefined_test_loan:
                                        continue
                                if self.loan_num_not_in_list(pending_loan_num):
                                    self.loans.append({'loan_number': pending_loan_num})
                                else:
                                    continue
                                is_any_green = True
                            elif 'color: red;' in days_due_col[count].get_attribute('style').lower():
                                print('Color is red for ' + str(loan_number_col[count].get_attribute('innerText')))
                        except Exception as e:
                            print(e)
                            com.take_screenshot(self.browser, str(e))
                        finally:
                            count = count + 1
                else:
                    print('No loans found')
                    exit(1)
                is_next_page = self.browser.does_page_contain_element(next_page_xpath)
                if is_next_page:
                    is_next_page_enabled = self.browser.find_element(next_page_xpath).get_attribute('disabled')
                    if is_next_page_enabled != 'true':
                        self.browser.click_element_when_visible(next_page_xpath)
                        self.browser.wait_until_element_is_not_visible('//img[@id="ctl00_ContentPlaceholderMain_imgWait"]', timedelta(0, 60))
                    else:
                        break
                else:
                    break

            # TODO: remove this before prod. ONLY FOR SINGLE TESTING LOANS
            if len(self.loans) < 1 and len(predefined_test_loan.split(',')) < 2:
                self.loans.append({'loan_number': predefined_test_loan})
                is_any_green = True

            if is_any_green:
                for loan_item in self.loans:
                    print('Obtaining data for loan ' + str(loan_item['loan_number']))
                    self.browser.input_text_when_element_is_visible("//input[contains(@id, 'ctl00_txtSearch')]", str(loan_item['loan_number']))
                    self.browser.click_element_when_visible("//input[contains(@id, 'ctl00_imgBtnLoanSearch')]")
                    com.wait_element(self.browser, "//td[contains(text(),'Loan Info')]")
                    self.browser.click_element_when_visible('//td[contains(@id, "Bankruptcy")]/span[@class="greenfont"]')
                    # navigate to tasks and check 1447
                    if self.test_run:
                        pass
                    else:
                        if not self.check_1447_task_completed():
                            loan_item['can_be_processed'] = False
                            continue
                        else:
                            loan_item['can_be_processed'] = True
                    self.browser.click_element_when_visible('//tr[td/span[@class="greenfont"]]/following-sibling::tr//a[text()="Default Loan Info"]')
                    com.wait_element(self.browser, "//span[text()='Bankruptcy - Default Loan Info']")
                    loan_item['referral_site'] = self.browser.find_element("//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_DLI_Bankruptcy1_txtRefState']").get_attribute('value')
                    loan_item['vest_in_the_name_of'] = self.browser.find_element("//textarea[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_DLI_Bankruptcy1_txtVestInTheNameOf']").get_attribute('title')
                    loan_item['loan_type'] = self.browser.find_element("//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txtLDLoanType']").get_attribute('value')
                    if 'conventional uninsured' in loan_item['loan_type'].lower():
                        loan_item['loan_type'] = 'Conventional Uninsured'
                    loan_item['case_number'] = self.browser.find_element("//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_DLI_Bankruptcy1_txtBKCaseNumber']").get_attribute('value')
                    loan_item['district'] = self.browser.find_element('//input[@id="ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_DLI_Bankruptcy1_txtDistrict"]').get_attribute('value')
                    loan_item['property_address_1'] = self.browser.find_element("//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txtLDAddress1']").get_attribute('value')
                    loan_item['property_address_2'] = self.browser.find_element("//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txtLDAddress2']").get_attribute('value')  # returns null if empty
                    loan_item['property_address_3'] = self.browser.find_element("//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txtLDAddress3']").get_attribute('value')  # returns null if empty
                    loan_item['city'] = self.browser.find_element("//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txtLDCity']").get_attribute('value')
                    loan_item['state'] = self.browser.find_element("//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txtLDState']").get_attribute('value')
                    loan_item['zip_code'] = self.browser.find_element("//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txtLDZip']").get_attribute('value')
                    loan_item['county'] = self.browser.find_element("//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txtLDCounty']").get_attribute('value')
                    # borrower related info:
                    loan_item['parties'] = []
                    i = 0
                    while i < 4:
                        if i == 0:
                            party_position = 'borrower'
                            prefix = 'PB'
                        else:
                            party_position = 'co_borrower_' + str(i)
                            prefix = 'CB' + str(i)
                        first_name = self.browser.find_element(f"//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txt{prefix}FirstName']").get_attribute('value')
                        middle_name = self.browser.find_element(f"//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txt{prefix}MiddleName']").get_attribute('value')
                        last_name = self.browser.find_element(f"//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txt{prefix}LastName']").get_attribute('value')
                        ssn = self.browser.find_element(f"//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txt{prefix}SSN']").get_attribute('value')
                        address_1 = self.browser.find_element(f"//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txt{prefix}Address1']").get_attribute('value')
                        address_2 = self.browser.find_element(f"//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txt{prefix}Address2']").get_attribute('value')
                        address_3 = self.browser.find_element(f"//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txt{prefix}Address3']").get_attribute('value')
                        city = self.browser.find_element(f"//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txt{prefix}City']").get_attribute('value')
                        state = self.browser.find_element(f"//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txt{prefix}State']").get_attribute('value')
                        zip = self.browser.find_element(f"//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txt{prefix}Zip']").get_attribute('value')
                        county = self.browser.find_element(f"//input[@id='ctl00_ctl00_ContentPlaceholderMain_ContentPlaceholderLoanManagement_txt{prefix}County']").get_attribute('value')
                        party_dict = {
                            'party_position': party_position,
                            'first_name': first_name,
                            'middle_name': middle_name,
                            'last_name': last_name,
                            'ssn': ssn,
                            'address_1': address_1,
                            'address_2': address_2,
                            'address_3': address_3,
                            'city': city,
                            'state': state,
                            'zip': zip,
                            'county': county
                        }
                        temp = party_dict.copy()
                        if temp['first_name'] != '':
                            loan_item['parties'].append(temp)
                        i += 1
                    root_path = os.environ.get("ROBOT_ROOT", os.getcwd())
                    path_to_folder = os.path.join(root_path, 'temp', loan_item['loan_number'])
                    loan_item['path_to_folder'] = path_to_folder
                    loan_item['files'] = {}
                    try:
                        os.mkdir(path_to_folder)
                    except OSError:
                        print("Creation of the directory %s failed" % path_to_folder)
                    else:
                        print("Successfully created the directory %s " % path_to_folder)
                    nopc_status = self.get_nopc_doc()
                    loan_item['files']['nopc'] = {}
                    if not nopc_status['downloaded']:
                        print('There are no NOPC documents on Tempo: ' + nopc_status['message'])
                        loan_item['files']['nopc']['downloaded'] = False
                    else:
                        new_filepath = os.path.join(path_to_folder, os.path.basename(nopc_status['path']))
                        os.rename(nopc_status['path'], new_filepath)
                        nopc_status['path'] = new_filepath
                        loan_item['files']['nopc']['downloaded'] = nopc_status['downloaded']
                        loan_item['files']['nopc']['path'] = nopc_status['path']
                        loan_item['files']['nopc']['filled_date'] = nopc_status['filled_date']
                    poc_status = self.get_poc_doc(loan_item['case_number'])
                    loan_item['files']['poc'] = {}
                    if not poc_status['downloaded']:
                        print('There are no POC documents on Tempo: ' + poc_status['message'])
                        loan_item['files']['poc']['downloaded'] = False
                    else:
                        new_filepath = os.path.join(path_to_folder, os.path.basename(poc_status['path']))
                        PDF().close_all_pdfs()
                        os.rename(poc_status['path'], new_filepath)
                        poc_status['path'] = new_filepath
                        loan_item['files']['poc']['downloaded'] = poc_status['downloaded']
                        loan_item['files']['poc']['path'] = poc_status['path']
                        loan_item['files']['poc']['filled_date'] = poc_status['filled_date']
                    if predefined_file_type != '':
                        temp_dict = self.get_escrow_or_arm(predefined_file_type)
                    else:
                        temp_dict = self.get_escrow_or_arm()
                    loan_item['doc_type'] = []
                    if temp_dict['file'] == 'escrow':
                        loan_item['files']['escrow'] = {}
                        new_filepath = os.path.join(path_to_folder, os.path.basename(temp_dict['path']))
                        os.rename(temp_dict['path'], new_filepath)
                        loan_item['files']['escrow']['downloaded'] = temp_dict['downloaded']
                        loan_item['files']['escrow']['path'] = new_filepath
                        try:
                            loan_item['files']['escrow']['path'] = self.redact_loan_number(new_filepath, loan_item['loan_number'])
                        except:
                            com.log_message('Unable to redact PDF, manual redaction required', 'ERROR')
                        loan_item['doc_type'].append('escrow')
                    else:
                        loan_item['files']['arm'] = {}
                        new_filepath = os.path.join(path_to_folder, os.path.basename(temp_dict['path']))
                        os.rename(temp_dict['path'], new_filepath)
                        loan_item['files']['arm']['downloaded'] = temp_dict['downloaded']
                        try:
                            loan_item['files']['arm']['path'] = self.redact_loan_number(new_filepath, loan_item['loan_number'])
                        except:
                            com.log_message('Unable to redact PDF, manual redaction required', 'ERROR')
                        loan_item['doc_type'].append('arm')
                    if loan_item['district'] == '':
                        loan_item['district'] = STATE_DISTRICT_MAPPING[loan_item['referral_site'].strip().upper()]
                    com.log_message('Bot successfully scraped data from Tempo')

    def get_nopc_doc(self) -> dict:
        return_dict = {}
        button_available = self.browser.is_element_visible('//a[contains(@id, "ctl00_hlnkECMS")]')
        if button_available:
            self.browser.click_element_when_visible('//a[contains(@id, "ctl00_hlnkECMS")]')
        else:
            self.browser.click_element_when_visible('//tr[contains(@id, "ctl00_trECMSMainLevel")]')
            self.browser.click_element_when_visible('//a[contains(@id, "ctl00_hlnkECMS")]')
        com.wait_element(self.browser, '//a[contains(text(), "Payment Change")]', 10)
        nopc_folder = self.browser.find_elements('//a[contains(text(), "Payment Change")]')
        if len(nopc_folder) > 0:
            nopc_folder[0].click()
            com.wait_element(self.browser, '//a[text()="Filed NOPC"]')
            self.browser.find_elements('//a[text()="Filed NOPC"]')[0].click()
            time.sleep(5)
            while True:
                try:
                    list_of_files = glob.glob(self.path_to_temp + '\*')
                    latest_file = max(list_of_files, key=os.path.getctime)
                    if 'crdownload' not in latest_file:
                        break
                except:
                    pass
            print(latest_file)
            try:
                p = PDF()
                p.open_pdf_document(latest_file)
                p.parse_pdf()
                pdf_content = p.get_text_from_pdf()
                if 'Filed' in pdf_content[1]:
                    filled_date = re.findall(r'(?:Filed.\s*)(\S*)(?:\s+)', pdf_content[1])[0].strip()
                    return_dict['downloaded'] = True
                    return_dict['path'] = latest_file
                    return_dict['filled_date'] = filled_date
                    return return_dict
                else:
                    p.close()
                    raise Exception
            except:
                try:  # using OCR
                    ocrp = OcrPdf(latest_file)
                    ocrp.prepare_amount_of_pages(2)
                    matches = ocrp.find_text_by_re(r'(?:[F|f]iled.[\s]{0,})(\S*)(?:\s+)')
                    for match in matches:
                        temp = re.match(r'\d{2}\/\d{2}\/\d{2,4}', match.replace(' ', ''))
                        if temp is not None:
                            return_dict['downloaded'] = True
                            return_dict['path'] = latest_file
                            return_dict['filled_date'] = match
                            return return_dict
                    return_dict['downloaded'] = False
                    return_dict['message'] = "Failed to parse the file."
                    return return_dict
                except:
                    return_dict['downloaded'] = False
                    return_dict['message'] = "Failed to parse the file."
                    return return_dict
        else:
            return_dict['downloaded'] = False
            return_dict['message'] = 'No such folder'
            return return_dict

    def get_poc_doc(self, case_number) -> dict:
        return_dict = {}
        self.navigate_to_ecms()
        poc_folders = self.browser.find_elements(f'//a[{com.contains_lower_xpath("proof of claim")}]')
        if len(poc_folders) > 0:
            if len(poc_folders) > 1:
                i = 0
                while i < len(poc_folders):
                    poc_folders = self.browser.find_elements(f'//a[{com.contains_lower_xpath("proof of claim")}]')
                    poc_folders[i].click()
                    i += 1
                    com.wait_element(self.browser, '//a[contains(text(), "Filed POC")]', 15)
                    poc_files = self.browser.find_elements('//a[contains(text(), "Filed POC")]')
                    if len(poc_files) > 0:
                        file_dict = self.iterate_poc_files(case_number)
                        if file_dict is not None:
                            return file_dict
                    self.navigate_to_ecms()
            else:
                poc_folders = self.browser.find_elements(f'//a[{com.contains_lower_xpath("proof of claim")}]')
                poc_folders[0].click()
                com.wait_element(self.browser, '//a[contains(text(), "Filed POC")]', 15)
                poc_files = self.browser.find_elements('//a[contains(text(), "Filed POC")]')
                if len(poc_files) > 0:
                    file_dict = self.iterate_poc_files(case_number)
                    if file_dict is not None:
                        return file_dict
        return_dict['downloaded'] = False
        return_dict['message'] = "Failed to find valid POC file"
        return return_dict

    def navigate_to_ecms(self):
        button_available = self.browser.is_element_visible('//a[contains(@id, "ctl00_hlnkECMS")]')
        if button_available:
            self.browser.click_element_when_visible('//a[contains(@id, "ctl00_hlnkECMS")]')
        else:
            self.browser.click_element_when_visible('//tr[contains(@id, "ctl00_trECMSMainLevel")]')
            self.browser.click_element_when_visible('//a[contains(@id, "ctl00_hlnkECMS")]')
        com.wait_element(self.browser, '//a[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "proof of claim")]', 10)

    def iterate_poc_files(self, case_number) -> dict or None:
        ret_dict = {}
        com.wait_element(self.browser, '//a[contains(text(), "Filed POC")]', 15)
        poc_files = self.browser.find_elements('//a[contains(text(), "Filed POC")]')
        for file in poc_files:
            file.click()
            time.sleep(5)
            while True:
                try:
                    list_of_files = glob.glob(self.path_to_temp + '\*')
                    latest_file = max(list_of_files, key=os.path.getctime)
                    if 'crdownload' not in latest_file:
                        break
                except:
                    pass
            print(latest_file)
            p_case_num, p_filed_date = ParsePDFDOcs.poc_case_number_parse(latest_file)
            if p_case_num == 'error' and p_filed_date == 'error':
                print('Not valid POC file detected')
                os.remove(latest_file)
            else:
                if case_number in p_case_num:
                    ret_dict['case_number'] = p_case_num
                    ret_dict['filled_date'] = p_filed_date
                    ret_dict['path'] = latest_file
                    ret_dict['downloaded'] = True
                    return ret_dict
                else:
                    os.remove(latest_file)
                    return None

    def get_escrow_or_arm(self, file_type: str = '') -> dict:
        return_dict = {}
        # check NEW buble
        button_available = self.browser.is_element_visible('//a[contains(@id, "ctl00_hlnkECMS")]')
        if button_available:
            self.browser.click_element_when_visible('//a[contains(@id, "ctl00_hlnkECMS")]')
        else:
            self.browser.click_element_when_visible('//tr[contains(@id, "ctl00_trECMSMainLevel")]')
            self.browser.click_element_when_visible('//a[contains(@id, "ctl00_hlnkECMS")]')

        com.wait_element(self.browser, '//span[@id="ctl00_ctl00_ContentPlaceholderMain_lblMasterName"]', 10)
        if self.browser.does_page_contain_element('//a[contains(@class, "new") and contains(text(), "Escrow Analysis")]') or file_type == "escrow":
            self.browser.click_element_when_visible('//a[contains(text(), "Escrow Analysis")]')
            files = self.browser.find_elements('//a[contains(text(), "BK Analysis")]')
            if len(files) > 0:
                files[0].click()
                time.sleep(5)
                while True:
                    try:
                        list_of_files = glob.glob(self.path_to_temp + '\*')
                        latest_file = max(list_of_files, key=os.path.getctime)
                        if 'crdownload' not in latest_file:
                            break
                    except:
                        pass
                path_to_file = latest_file
                print("Escrow Analysis - BK Analysis - " + path_to_file)
                return_dict['file'] = 'escrow'
                return_dict['downloaded'] = True
                return_dict['path'] = latest_file
                return return_dict
            else:
                print("'BK Analysis' files were not appeared")
                return_dict['file'] = 'escrow'
                return_dict['downloaded'] = False
                return_dict['path'] = ''
                return return_dict

        elif self.browser.does_page_contain_element('//a[contains(@class, "new") and contains(text(), "Bankruptcy Miscellaneous")]') or file_type == "arm":
            self.browser.click_element_when_visible('//a[contains(text(), "Bankruptcy Miscellaneous")]')
            files = self.browser.find_elements('//a[contains(text(), "ARM Change")]')
            if len(files) > 0:
                files[0].click()
                time.sleep(5)
                while True:
                    try:
                        list_of_files = glob.glob(self.path_to_temp + '\*')
                        latest_file = max(list_of_files, key=os.path.getctime)
                        if 'crdownload' not in latest_file:
                            break
                    except:
                        pass
                path_to_file = latest_file
                print("Bankruptcy Miscellaneous - ARM Change - " + path_to_file)
                return_dict['file'] = 'arm'
                return_dict['downloaded'] = True
                return_dict['path'] = latest_file
                return return_dict
            else:
                print("'ARM Change' files were not appeared")
                return_dict['file'] = 'arm'
                return_dict['downloaded'] = False
                return_dict['path'] = ''
                return return_dict
        else:
            raise Exception("Element with red NEW Bubble wasn't appeared")

    def redact_loan_number(self, in_file, loan_number):
        filename_base = in_file.replace(os.path.splitext(in_file)[1], "")
        new_path = filename_base + "_redacted.pdf"
        doc = fitz.open(in_file)
        for page in doc:
            sensitive = get_sensitive_data(page.get_text("").split('\n'), loan_number)
            for data in sensitive:
                areas = page.search_for(data)
                [page.addRedactAnnot(area, fill=(0, 0, 0)) for area in areas]
            page.apply_redactions()
        doc.save(new_path)
        print("Successfully redacted")
        return new_path

    def close_task_1448(self, loan_number: str):
        try:
            self.browser.input_text_when_element_is_visible("//input[contains(@id, 'ctl00_txtSearch')]", loan_number)
            try:
                self.browser.click_element_when_visible("//input[contains(@id, 'ctl00_imgBtnLoanSearch')]")
            except Exception as ex:
                com.log_message('Error in click_search_loan flow:', 'TRACE')
                com.log_message(str(ex), 'TRACE')
                traceback.print_exc()
                com.take_screenshot(self.browser, 'click_search_loan_exception')
                com.log_DOM(self.browser)
                try:
                    self.browser.driver.find_elements_by_xpath('//input[contains(@id, "ctl00_txtSearch")]')[0].send_keys(Keys.ENTER)
                except Exception as ey:
                    com.log_message('Error in send_enter_key flow:', 'TRACE')
                    com.log_message(str(ey), 'TRACE')
                    traceback.print_exc()
                    com.take_screenshot(self.browser, 'send_enter_key_exception')
                    com.log_DOM(self.browser)
                    return
            com.wait_element(self.browser, "//td[contains(text(),'Loan Info')]")
            self.browser.click_element_when_visible('//td[contains(@id, "Bankruptcy")]/span[@class="greenfont"]')
            com.wait_element(self.browser, '//tr[td[contains(@id, "Bankruptcy")] and td/span[@class="greenfont"]]/following-sibling::tr//a[contains(text(), "Tasks")]')
            self.browser.click_element_when_visible('//tr[td[contains(@id, "Bankruptcy")] and td/span[@class="greenfont"]]/following-sibling::tr//a[contains(text(), "Tasks")]')
            self.browser.click_element_when_visible('//td[span[contains(text(),"1448") and contains(@id, "lblEvtNumber")]]/following-sibling::td/table//td/input[contains(@id, "imgClose")]')
            self.browser.input_text_when_element_is_visible('//input[contains(@id, "txtDatemp")]', datetime.today().strftime("%m/%d/%Y"))
            self.browser.input_text_when_element_is_visible('//textarea[contains(@id, "txtCloseReason")]', 'Referral received and reviewed')
            self.browser.select_from_list_by_value('//select[contains(@id, "DRP")]', 'No Remediation Required')
            if self.test_run:
                print('Save button placeholder')
            else:
                self.browser.click_element_when_visible('//input[contains(@id, "btnSaveDummy")]')
            com.log_message('Task 1448 Closed for ' + loan_number)
            time.sleep(30)
        except Exception as ex:
            com.log_message('Error in close_1448 flow:', 'TRACE')
            com.log_message(str(ex), 'TRACE')
            traceback.print_exc()
            com.take_screenshot(self.browser, 'close_1448_exception')
            com.log_DOM(self.browser)

    def close_logout(self):
        try:
            self.browser.click_element_when_visible('//a[contains(@id, "ctl00_lnkLogOut")]')
            self.browser.close_window()
            self.is_site_available = False
            print('Logged out')
        except:
            pass

    def loan_num_not_in_list(self, pending_loan_num: str) -> bool:
        result = True
        for loan_item in self.loans:
            if pending_loan_num in loan_item['loan_number']:
                result = False
        return result
