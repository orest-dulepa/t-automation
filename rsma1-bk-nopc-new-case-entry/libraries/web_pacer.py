import glob
from PyPDF2 import PdfFileMerger
from RPA.Browser.Selenium import Selenium
from libraries import common as com
from RPA.PDF import PDF
from decimal import Decimal
from re import sub
from datetime import datetime as dt
from datetime import timedelta as td
import os
import re
import time
import datetime
import base64
import json


class Pacer:
    def __init__(self, credentials: dict):
        self.browser: Selenium = Selenium()
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.client_code: str = 'BOT'
        self.is_site_available: bool = False
        self.parsed_data: dict = {}
        self.claims_all: dict = {}
        self.path_to_temp: str = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp')
        self.browser.set_download_directory(self.path_to_temp, True)
        self.path_to_html: str = os.path.join(self.path_to_temp, 'pacer.html')
        self.path_to_pdf: str = os.path.join(self.path_to_temp, 'pacer.pdf')
        self.path_to_claims: str = os.path.join(self.path_to_temp, 'claims.html')
        self.path_to_claims_pdf: str = os.path.join(self.path_to_temp, 'claims.pdf')

    def login_to_pacer(self):
        self.is_site_available = False
        try_count = 1
        self.browser.close_browser()

        while try_count <= 3 and self.is_site_available is False:
            try:
                self.browser.open_available_browser(self.url, headless=True)
                self.browser.set_window_size(1920, 1080)

                com.wait_element(self.browser, '//input[@id="loginForm:loginName"]')
                self.browser.input_text_when_element_is_visible('//input[@id="loginForm:loginName"]', self.login)
                self.browser.input_text_when_element_is_visible('//input[@id="loginForm:password"]', self.password)
                self.browser.input_text_when_element_is_visible('//input[@id="loginForm:clientCode"]', self.client_code)

                self.browser.click_element_when_visible('//button[@id="loginForm:fbtnLogin"]')

                com.wait_element(self.browser, '//div[@id="regmsg:chkRedact"]')
                self.browser.click_element_when_visible('//div[@id="regmsg:chkRedact"]')
                com.wait_element(self.browser, '//button[@id="regmsg:bpmConfirm" and @aria-disabled="false"]')
                self.browser.click_element_when_visible('//button[@id="regmsg:bpmConfirm" and @aria-disabled="false"]')

                com.wait_element(self.browser, '//div[@id="pnlBreadCrumb"]')
                self.is_site_available = self.browser.does_page_contain_element('//div[@id="pnlBreadCrumb"]')
            except Exception as ex:
                com.log_message("Logging into Pacer National Website. Attempt #{} failed".format(try_count), 'ERROR')
                print(str(ex))
                self.browser.capture_page_screenshot(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output',
                                                                  'Pacer_login_failed_{}.png'.format(try_count)))
                self.browser.close_browser()
            finally:
                if not self.is_site_available:
                    self.browser.close_browser()
                try_count += 1
        self.browser.timeout = 45

    def parse_data_from_page(self):
        self.parsed_data = {}
        judge_replacement = ['Chief Judge', 'The Honorable Judge', 'The Honorable', 'Honorable Judge', 'Judge', 'Honorable', 'Hon.', 'BayCity', 'Bay City', 'baycity', 'bay city']
        # Get Court Name
        bankruptcy_court: str = self.browser.get_text('//b/font')
        self.parsed_data['Court Name'] = bankruptcy_court.split('\n')[1]
        self.parsed_data['Bankruptcy Petition #'] = bankruptcy_court.split('#:')[-1].strip().replace(' ', '')
        temp = str(
            re.findall(r'Assigned to: (|Judge)(.+)\n', self.browser.get_text('//td[contains(., "Assigned to")]'))[0][1]).strip()
        for a in judge_replacement:
            temp = temp.replace(a, '').strip()
        self.parsed_data['Assigned to'] = temp

        self.parsed_data['Debtor'] = []
        debtors: list = self.browser.find_elements('//td[contains(., "Debtor")]')
        for debtor in debtors:
            try:
                debtor_array: str = debtor.text.split('\n')
                if len(debtor_array) < 4:
                    continue
                debtor_name: str = debtor_array[1].strip()
                debtor_address: str = debtor_array[2].strip()
                debtor_zip: str = debtor_array[3].strip()

                debtor_county: str = ''
                if 'ssn' not in debtor_array[4].lower():
                    debtor_county: str = debtor_array[4].strip()

                debtor_ssn: str = ''
                for item in debtor_array:
                    if 'ssn' in item.lower():
                        debtor_ssn: str = item.split(':')[-1].strip()

                if ',' in debtor_name:
                    debtor_name = debtor_name.split(',')[0]
                d_name_parts = debtor_name.split(' ')
                d_fname = d_name_parts[0]
                d_lname = d_name_parts[len(d_name_parts) - 1]
                d_name_parts.pop()
                d_name_parts.pop(0)
                d_mname = ' '.join(d_name_parts)
                if debtor_county != '':
                    temp_state = debtor_county.split('-')[1]
                    temp_county = debtor_county.split('-')[0].lower().capitalize()
                    temp_zip = debtor_zip.split(temp_state)[1].strip()
                else:
                    temp_state = debtor_zip.split(' ')[1].strip()
                    temp_county = ''
                    temp_zip = debtor_zip.split(' ')[2].strip()
                temp_city = debtor_zip.split(',')[0].lower().capitalize()
                self.parsed_data['Debtor'].append({
                    'name': debtor_name,
                    'address': debtor_address,
                    'zip': debtor_zip,
                    'county': debtor_county,
                    'ssn': debtor_ssn,

                    'parsed_first_name': d_fname,
                    'parsed_last_name': d_lname,
                    'parsed_middle_name': d_mname,
                    'parsed_state': temp_state,
                    'parsed_county': temp_county,
                    'parsed_zip': temp_zip,
                    'parsed_city': temp_city
                })
            except:
                pass

        debtor_attys: list = self.browser.find_elements('//td[contains(., "Debtor")]/following-sibling::td[font[contains(text(), "represented by")]]/following-sibling::td')
        for atty in debtor_attys:
            try:
                atty_array = atty.text.split('\n')
                self.parsed_data['Debtor Attorney'] = atty_array[0].strip()
                tmp_arr = atty_array.copy()
                self.parsed_data['Debtor Attorney other'] = tmp_arr
                break
            except:
                pass

        self.parsed_data['Trustee'] = []
        trustees: list = self.browser.find_elements('//td//b[text()="Trustee"]/../..')
        for trustee in trustees:
            trustee_data: str = trustee.text.split('\n')
            try:
                skip_flag = False
                for t_data in trustee_data:
                    if 'terminated' in t_data.lower():
                        skip_flag = True
                if skip_flag:
                    continue
                else:
                    self.parsed_data['Trustee'].append(trustee_data[1].strip())
            except:
                self.parsed_data['Trustee'].append(trustee_data[1].strip())

        if self.browser.does_page_contain_element('//td//b[text()="U.S. Trustee"]'):
            us_trustee: str = str(self.browser.find_element('//td//b[text()="U.S. Trustee"]/../..').text).split('\n')[1]
            self.parsed_data['U.S. Trustee'] = us_trustee
            self.parsed_data['U.S. Trustee other'] = str(self.browser.find_element('//td//b[text()="U.S. Trustee"]/../..').text).split('\n')
            if len(self.parsed_data['U.S. Trustee other']) < 3:
                self.parsed_data['U.S. Trustee other'] = str(self.browser.find_element('//td//b[text()="U.S. Trustee"]/../../../following-sibling::td[font[contains(text(), "represented by")]]/following-sibling::td').text).split('\n')

    def search_case(self, case_number: str, parties: list, district: str):
        com.wait_element(self.browser, '//a[@id="frmSearch:findCasesAdvanced"]')
        self.browser.click_element_when_visible('//a[@id="frmSearch:findCasesAdvanced"]')

        com.wait_element(self.browser, '//div[@id="frmSearch:ddCourtType"]//span[contains(@class, "ui-icon-triangle-1-s")]')
        self.browser.click_element_when_visible('//div[@id="frmSearch:ddCourtType"]//span[contains(@class, "ui-icon-triangle-1-s")]')
        self.browser.wait_until_page_does_not_contain_element('//div[@id="dlgAjaxActivity" and @aria-hidden="false"]', td(0, 60))
        com.wait_element(self.browser, '//li[@data-label="Bankruptcy"]')
        self.browser.click_element_when_visible('//li[@data-label="Bankruptcy"]')
        self.browser.wait_until_page_does_not_contain_element('//div[@id="dlgAjaxActivity" and @aria-hidden="false"]', td(0, 60))
        # Not working
        # com.wait_element(self.browser, '//select[@name="frmSearch:ddCourtType_input"]')
        # self.browser.select_from_list_by_value('//select[@name="frmSearch:ddCourtType_input"]', 'bk')  # Bankruptcy

        self.browser.wait_until_page_does_not_contain_element('//div[@id="dlgAjaxActivity" and @aria-hidden="false"]', td(0, 60 * 2))
        com.wait_element(self.browser, '//input[@id="frmSearch:txtCaseNumber"]')
        self.browser.input_text_when_element_is_visible('//input[@id="frmSearch:txtCaseNumber"]', case_number)

        self.browser.click_element_when_visible('//button/span[text()="Search"]/..')

        com.wait_element(self.browser, '//tr[contains(@class, "ui-datatable")]')
        rows = self.browser.find_elements('//tr[contains(@class, "ui-datatable")]')
        case_number = ''
        defining_term = ''
        is_last_name_match = False
        for row in rows:
            tmp_row_text = str(row.text).lower().replace(' ', '')
            for party in parties:
                if party['last_name'].lower() in tmp_row_text:
                    list_of_column = row.get_property('innerText').split('\t')
                    case_number = str(list_of_column[3]).strip()
                    defining_term = party['last_name'].lower()
                    is_last_name_match = True
                    break
                elif district.lower() in tmp_row_text and party['first_name'].lower() in tmp_row_text:
                    list_of_column = row.get_property('innerText').split('\t')
                    case_number = str(list_of_column[3]).strip()
                    defining_term = district.lower()
                    break
            if defining_term != '':
                break
        if case_number == '':
            print('Case not found')
            return False

        if is_last_name_match:
            self.browser.click_element_when_visible(
                f'//tr/td[span[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ ", "abcdefghijklmnopqrstuvwxyz"),"{defining_term}")]]/following-sibling::td//a[text()="{case_number}"]')
        else:
            self.browser.click_element_when_visible(
                f'//tr/td[span[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ ", "abcdefghijklmnopqrstuvwxyz"),"{defining_term}")]]/preceding-sibling::td//a[text()="{case_number}"]')
        browser_tabs = self.browser.get_window_handles()
        self.browser.switch_window(browser_tabs[1])
        self.browser.set_window_size(1920, 1080)

        com.wait_element(self.browser, '//a[contains(text(), "Docket Report")]')
        self.browser.click_element_when_visible('//a[contains(text(), "Docket Report")]')

        com.wait_element(self.browser, '//b[text()="Docket Sheet"]')
        com.wait_element(self.browser, '//input[@id="date_from"]')
        self.browser.input_text_when_element_is_visible('//input[@id="date_from"]',
                                                        (datetime.date.today() + td(-4 * 30)).strftime(
                                                            '%m/%d/%Y'))
        self.browser.input_text_when_element_is_visible('//input[@id="date_to"]',
                                                        datetime.date.today().strftime('%m/%d/%Y'))
        self.browser.click_element_when_visible('//input[@value="Run Report"]')

        com.wait_element(self.browser, '//font[contains(., "PACER Service Center")]')
        try:
            self.browser.click_element_when_visible('//input[@value="Run Report"]')
            com.wait_element(self.browser, '//font[contains(., "PACER Service Center")]')
        except:
            pass

        source = self.browser.get_source()
        source = source.replace('/css/default.css', os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'pacer', 'default.css'))  # os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'pacer', 'default.css')
        f = open(self.path_to_html, "a")
        f.write(source)
        f.close()

        self.generate_pdf_with_webdriver(self.path_to_html, self.path_to_pdf)
        com.log_message('Report successfully downloaded')

        self.parse_data_from_page()

        claims_reg = self.browser.does_page_contain_element('//a[contains(text(), "Claims Register")]')
        if claims_reg:
            self.browser.click_element_when_visible('//a[contains(text(), "Claims Register")]')
            com.wait_element(self.browser, '//h3[text()="Claims Register Summary"]')

            self.parse_claims_page()

            source = self.browser.get_source()
            source = source.replace('/css/default.css', os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'pacer', 'claims.css'))
            f = open(self.path_to_claims, "a")
            f.write(source)
            f.close()

            self.generate_pdf_with_webdriver(self.path_to_claims, self.path_to_claims_pdf)
            com.log_message('Claims document successfully downloaded')
        else:
            com.log_message('Claims register does not present on pacer')
        return True

    @staticmethod
    def generate_pdf_with_webdriver(path_in, path_out):
        selenium_lib = Selenium()
        selenium_lib.open_available_browser(f"file://{path_in}", headless=True)
        driver = selenium_lib.driver

        def get_pdf_from_html():
            params = {
                "landscape": False,
                "displayHeaderFooter": True,
                "printBackground": True,
                "preferCSSPageSize": True,
            }
            result = send_command("Page.printToPDF", params)
            return base64.b64decode(result["data"])

        def send_command(cmd, params):
            resource = f"session/{driver.session_id}/chromium/send_command_and_get_result"
            url = f"{driver.command_executor._url}/{resource}"
            body = json.dumps({"cmd": cmd, "params": params})
            response = driver.command_executor._request("POST", url, body)

            return response.get("value")

        pdf = get_pdf_from_html()
        with open(path_out, "wb") as f:
            f.write(pdf)
        selenium_lib.close_browser()

    def parse_pdf(self):
        pdf_reader = PDF()
        pdf_reader.parse_pdf(self.path_to_pdf)

        pages = pdf_reader.rpa_pdf_document.get_pages()
        page = pages[1]

        for line in range(len(page.content)):
            try:
                current_line_text = str(page.content[line].text)
            except:
                continue
            try:
                if current_line_text.lower().startswith('U.S. Bankruptcy Court'.lower()):
                    self.parsed_data['Court Name'] = re.search(
                        r'(?i)(?<=U\.S\. Bankruptcy Court)(\s*.+\n)(Bankruptcy Petition)', current_line_text)[1].strip()
                    self.parsed_data['State'] = re.search(r'(?i)(?<=of)\s*\w+\s*[^(]', current_line_text)[0].strip()
                    self.parsed_data['City'] = re.search(r'(?i)(\()(.*)(\))', current_line_text)[2].strip()
                    self.parsed_data['Bankruptcy Petition #'] = re.search(r'(?i)Bankruptcy Petition #:(.*)$', current_line_text)[1].strip()
                if 'Date filed'.lower() in current_line_text.lower():
                    self.parsed_data['Date filed'] = re.search(r'(?i)Date filed:(.*)(\n|$)', current_line_text)[1].strip()
                if 'Plan confirmed'.lower() in current_line_text.lower():
                    self.parsed_data['Plan confirmed'] = re.search(r'(?i)Plan confirmed:(.*)(\n|$)', current_line_text)[1].strip()
                if 'Assigned to'.lower() in current_line_text.lower():
                    self.parsed_data['Assigned to'] = re.search(r'(?i)Assigned to:.*Judge(.*)(\n|$)', current_line_text)[1].strip()
                    self.parsed_data['Chapter'] = re.search(r'(?i)Chapter (.*)(\n|$)', current_line_text)[0].strip()
                if 'Trustee'.lower() in current_line_text.lower() and 'Trustee' not in self.parsed_data:
                    self.parsed_data['Trustee'] = re.search(r'(?i)Trustee\n(.*)(\n|$)', current_line_text)[1].strip()
                if 'Debtor'.lower() in current_line_text.lower():
                    if 'Debtor' not in self.parsed_data:
                        self.parsed_data['Debtor'] = []
                    debtor_name = re.search(r'(?i)Debtor(\s*\d*)\n(.*)\n', current_line_text)[2].strip()
                    if debtor_name not in self.parsed_data['Debtor']:
                        self.parsed_data['Debtor'].append(debtor_name)
                if 'Represented by'.lower() in current_line_text.lower():
                    if 'Represented by' not in self.parsed_data:
                        self.parsed_data['Represented by'] = []
                    represented_by_name = re.search(r'(?i)Represented by(.*)', current_line_text)[1].strip()
                    if represented_by_name not in self.parsed_data['Represented by']:
                        self.parsed_data['Represented by'].append(represented_by_name)
            except Exception as ex:
                print(repr(page.content[line].text))
                print(str(ex))
                print(line)
        pdf_reader.close_all_pdf_documents()

    def parse_claims_page(self):
        self.claims_all = {}
        claims_creditors = self.browser.find_elements('//td[@align="left"]/font[i[contains(text(),"Creditor")]]')
        claims_numbers = self.browser.find_elements('//td[@align="left"]/font/b[contains(text(),"Claim No:")]')
        # sometimes there are 'Secured claimed' or 'Priority claimed' so filter them out
        claims_amount = self.browser.find_elements('//table[@class="complexReport"]//tr[2]//table/tbody/tr[td/font[contains(text(), "claimed")]]')
        all_histories = self.browser.find_elements('//td/font/i[contains(., "History")]')
        i = 0
        skip_i = 0
        while i < len(claims_numbers):
            self.claims_all[i + 1] = {}
            self.claims_all[i + 1]['number'] = claims_numbers[i].text.replace('Claim No: ', '').lower().strip()
            self.claims_all[i + 1]['creditor'] = claims_creditors[i].text.lower().strip()
            if 'Secured claimed' in claims_amount[i].text:
                skip_i = skip_i + 1
            if 'Priority claimed' in claims_amount[i].text:
                skip_i = skip_i + 1
            self.claims_all[i + 1]['amount'] = claims_amount[i + skip_i].text
            self.claims_all[i + 1]['history'] = all_histories[i].text.lower()
            i += 1

    def get_claim_no_by_creditor(self, creditor: str) -> str:
        creditor_counter = 0
        match_list = []
        for item in self.claims_all:
            if self.is_creditor_in_row(creditor, self.claims_all[item]['creditor']) and 'withdrawal of claim' not in self.claims_all[item]['history']:
                creditor_counter = creditor_counter + 1
                match_list.append(item)
        if creditor_counter < 1:
            return '-1'
        elif creditor_counter > 1:
            max_amount = Decimal(sub(r'[^\d.]', '', self.claims_all[match_list[0]]['amount']))
            max_index = match_list[0]
            for item in match_list:
                temp_amount = Decimal(sub(r'[^\d.]', '', self.claims_all[item]['amount']))
                if temp_amount > max_amount:
                    max_amount = temp_amount
                    max_index = item
            return str(max_index)
        else:
            return str(match_list[0])

    def is_creditor_in_row(self, creditor: str, row: str) -> bool:
        cred_parts = creditor.split(' ')
        cred_parts_num = len(cred_parts)
        match_num = 0
        for cr_part in cred_parts:
            if cr_part.lower().strip() in row.lower().strip():
                match_num += 1
        if match_num == cred_parts_num:
            return True
        else:
            return False

    def get_doc_type_to_use(self, claim_number: str) -> str:
        doc_desc = self.browser.find_elements(f'//table[@class="complexReport"][{claim_number}]//td[@align="left" and font[i[contains(text(),"History")]]]//tr/td[5]')
        dates = self.browser.find_elements(f'//table[@class="complexReport"][{claim_number}]//td[@align="left" and font[i[contains(text(),"History")]]]//tr/td[4]')
        i = 0
        latest_file_desc = ''
        latest_file_date = dt.strptime('01/01/2000', "%m/%d/%Y")
        for file_desc in doc_desc:
            curr_desc = file_desc.text.lower()
            p_date = dt.strptime(dates[i].text, "%m/%d/%Y")
            com.log_message("Processing file: " + curr_desc + ", date " + str(p_date), 'TRACE')
            i += 1
            if p_date > latest_file_date:
                if 'withdrawal of' in curr_desc or 'transfer of' in curr_desc or 'forbearance' in curr_desc:
                    com.log_message("Skipping file", 'TRACE')
                    continue
                if 'notice of' in curr_desc and 'payment change' in curr_desc:
                    com.log_message("NOPC detected", 'TRACE')
                    latest_file_desc = 'nopc'
                    latest_file_date = p_date
                elif curr_desc.startswith('claim'):
                    com.log_message("POC detected", 'TRACE')
                    latest_file_desc = 'poc'
                    latest_file_date = p_date
        com.log_message("Picked file: " + latest_file_desc + ", filed " + str(latest_file_date), 'TRACE')
        return latest_file_desc

    def download_file_by_claim_number_and_date(self, claim_number: str, files_from_tempo: dict, doc_type: list) -> [str, str]:
        dates = self.browser.find_elements(f'//table[@class="complexReport"][{claim_number}]//td[@align="left" and font[i[contains(text(),"History")]]]//tr/td[4]')
        doc_links = self.browser.find_elements(f'//table[@class="complexReport"][{claim_number}]//td[@align="left" and font[i[contains(text(),"History")]]]//tr/td[3]')
        doc_desc = self.browser.find_elements(f'//table[@class="complexReport"][{claim_number}]//td[@align="left" and font[i[contains(text(),"History")]]]//tr/td[5]')
        i = 0
        most_recent_nopc_date = dt.strptime('01/01/2000', "%m/%d/%Y")
        most_recent_nopc_file = None
        most_recent_poc_date = dt.strptime('01/01/2000', "%m/%d/%Y")
        most_recent_poc_file = None
        for file_desc in doc_desc:
            curr_desc = file_desc.text.lower()
            if 'withdrawal of' in curr_desc or 'transfer of' in curr_desc:
                continue
            if 'notice of' in curr_desc and 'payment change' in curr_desc and 'nopc' in doc_type:
                if 'filled_date' in files_from_tempo['nopc']:
                    p_date = dt.strptime(dates[i].text, "%m/%d/%Y")
                    try:
                        o_date = dt.strptime(files_from_tempo['nopc']['filled_date'], "%m/%d/%Y")
                    except:
                        o_date = dt.strptime(files_from_tempo['nopc']['filled_date'], "%m/%d/%y")
                    if p_date > o_date:
                        doc_links[i].click()
                        com.wait_element(self.browser, '//input[@type="submit" and @value="View Document"]')
                        com.take_screenshot(self.browser, 'pacer_download_file_1')
                        is_multiple_files = self.browser.does_page_contain_element(f'//p[{com.contains_lower_xpath("document selection menu")}]')
                        if is_multiple_files:
                            main_doc_lnks = self.browser.find_elements(
                                f'//td[{com.contains_lower_xpath("main document")}]/preceding-sibling::td[a]')
                            if len(main_doc_lnks) > 0:
                                main_doc_lnks[0].click()
                                com.wait_element(self.browser, '//input[@type="submit" and @value="View Document"]')
                                com.take_screenshot(self.browser, 'pacer_download_attachment')
                                is_button = self.browser.does_page_contain_element(
                                    '//input[@type="submit" and @value="View Document"]')
                                if is_button:
                                    self.browser.click_element_when_visible(
                                        '//input[@type="submit" and @value="View Document"]')
                            else:
                                com.take_screenshot(self.browser, "main_doc_not_available")
                                com.log_message('No main doc available', 'TRACE')
                        else:
                            if self.browser.does_page_contain_element('//input[@type="submit" and @value="View Document"]'):
                                self.browser.click_element_when_visible('//input[@type="submit" and @value="View Document"]')
                            else:
                                com.log_message('No view document found', 'TRACE')

                        latest_file = self.wait_for_file_download()
                        return 'nopc', latest_file
                else:
                    p_date = dt.strptime(dates[i].text, "%m/%d/%Y")
                    if p_date > most_recent_nopc_date:
                        most_recent_nopc_date = p_date
                        most_recent_nopc_file = doc_links[i]
            elif curr_desc.startswith('claim') and not files_from_tempo['poc']['downloaded'] and 'poc' in doc_type:
                if 'filled_date' in files_from_tempo['poc']:
                    p_date = dt.strptime(dates[i].text, "%m/%d/%Y")
                    try:
                        o_date = dt.strptime(files_from_tempo['poc']['filled_date'], "%m/%d/%Y")
                    except:
                        o_date = dt.strptime(files_from_tempo['poc']['filled_date'], "%m/%d/%y")
                    if p_date > o_date:
                        doc_links[i].click()
                        is_multiple_files = self.browser.does_page_contain_element(f'//p[{com.contains_lower_xpath("document selection menu")}]')
                        main_file = ''
                        att_file = ''
                        if is_multiple_files:
                            main_doc_lnks = self.browser.find_elements(f'//td[{com.contains_lower_xpath("main document")}]/preceding-sibling::td[a]')
                            attach_lnks = self.browser.find_elements(f'//td[{com.contains_lower_xpath("mortgage attachment")}]/preceding-sibling::td[a]')
                            if len(main_doc_lnks) > 0:
                                main_doc_lnks[0].click()
                                com.wait_element(self.browser, '//input[@type="submit" and @value="View Document"]')
                                com.take_screenshot(self.browser, 'pacer_download_attachment')
                                is_button = self.browser.does_page_contain_element('//input[@type="submit" and @value="View Document"]')
                                if is_button:
                                    self.browser.click_element_when_visible('//input[@type="submit" and @value="View Document"]')
                                    main_file = self.wait_for_file_download()
                            else:
                                com.take_screenshot(self.browser, "main_doc_not_available")
                                print('No main doc available')
                            if len(attach_lnks) > 0:
                                attach_lnks[0].click()
                                com.wait_element(self.browser, '//input[@type="submit" and @value="View Document"]')
                                com.take_screenshot(self.browser, 'pacer_download_main_doc')
                                is_button = self.browser.does_page_contain_element('//input[@type="submit" and @value="View Document"]')
                                if is_button:
                                    self.browser.click_element_when_visible('//input[@type="submit" and @value="View Document"]')
                                    att_file = self.wait_for_file_download()
                            else:
                                com.take_screenshot(self.browser, "mortgage_attachment_not_available")
                                print('No mortgage attachment available')
                        else:
                            is_button = self.browser.does_page_contain_element('//input[@type="submit" and @value="View Document"]')
                            if is_button:
                                self.browser.click_element_when_visible('//input[@type="submit" and @value="View Document"]')
                                latest_file = self.wait_for_file_download()
                            else:

                                if main_file != '' and att_file != '':
                                    latest_file = self.merge_poc_document(main_file, att_file)
                                else:
                                    latest_file = ''
                            return 'poc', latest_file
                else:
                    p_date = dt.strptime(dates[i].text, "%m/%d/%Y")
                    if p_date > most_recent_poc_date:
                        most_recent_poc_date = p_date
                        most_recent_poc_file = doc_links[i]
            i += 1
        if most_recent_nopc_file is not None:
            most_recent_nopc_file.click()
            com.wait_element(self.browser, '//input[@type="submit" and @value="View Document"]', 30)
            is_button = self.browser.does_page_contain_element('//input[@type="submit" and @value="View Document"]')
            if is_button:
                com.wait_element(self.browser, '//input[@type="submit" and @value="View Document"]')
                self.browser.click_element_when_visible('//input[@type="submit" and @value="View Document"]')
            else:
                is_multiple_files = self.browser.does_page_contain_element(
                    f'//p[{com.contains_lower_xpath("document selection menu")}]')
                if is_multiple_files:
                    main_doc_lnks = self.browser.find_elements(
                        f'//td[{com.contains_lower_xpath("main document")}]/preceding-sibling::td[a]')
                    if len(main_doc_lnks) > 0:
                        main_doc_lnks[0].click()
                        com.wait_element(self.browser, '//input[@type="submit" and @value="View Document"]')
                        com.take_screenshot(self.browser, 'pacer_download_attachment')
                        is_button = self.browser.does_page_contain_element(
                            '//input[@type="submit" and @value="View Document"]')
                        if is_button:
                            self.browser.click_element_when_visible(
                                '//input[@type="submit" and @value="View Document"]')
                    else:
                        com.take_screenshot(self.browser, "main_doc_not_available")
                        print('No main doc available')
            latest_file = self.wait_for_file_download()
            return 'nopc', latest_file
        elif most_recent_poc_file is not None:
            most_recent_poc_file.click()
            com.wait_element(self.browser, '//input[@type="submit" and @value="View Document"]', 30)
            is_button = self.browser.does_page_contain_element(
                '//input[@type="submit" and @value="View Document"]')
            if is_button:
                com.wait_element(self.browser, '//input[@type="submit" and @value="View Document"]')
                self.browser.click_element_when_visible('//input[@type="submit" and @value="View Document"]')
                latest_file = self.wait_for_file_download()
            else:
                is_multiple_files = self.browser.does_page_contain_element(
                    f'//p[{com.contains_lower_xpath("document selection menu")}]')
                main_file = ''
                att_file = ''
                if is_multiple_files:
                    main_doc_lnks = self.browser.find_elements(
                        f'//td[{com.contains_lower_xpath("main document")}]/preceding-sibling::td[a]')
                    attach_lnks = self.browser.find_elements(
                        f'//td[{com.contains_lower_xpath("mortgage attachment")}]/preceding-sibling::td[a]')
                    if len(main_doc_lnks) > 0:
                        main_doc_lnks[0].click()
                        com.wait_element(self.browser, '//input[@type="submit" and @value="View Document"]')
                        com.take_screenshot(self.browser, 'pacer_download_attachment')
                        is_button = self.browser.does_page_contain_element(
                            '//input[@type="submit" and @value="View Document"]')
                        if is_button:
                            self.browser.click_element_when_visible(
                                '//input[@type="submit" and @value="View Document"]')
                            main_file = self.wait_for_file_download()
                    else:
                        com.take_screenshot(self.browser, "main_doc_not_available")
                        print('No main doc available')
                    if len(attach_lnks) > 0:
                        attach_lnks[0].click()
                        com.wait_element(self.browser, '//input[@type="submit" and @value="View Document"]')
                        com.take_screenshot(self.browser, 'pacer_download_main_doc')
                        is_button = self.browser.does_page_contain_element(
                            '//input[@type="submit" and @value="View Document"]')
                        if is_button:
                            self.browser.click_element_when_visible(
                                '//input[@type="submit" and @value="View Document"]')
                            att_file = self.wait_for_file_download()
                    else:
                        com.take_screenshot(self.browser, "mortgage_attachment_not_available")
                        print('No mortgage attachment available')
                if main_file != '' and att_file != '':
                    latest_file = self.merge_poc_document(main_file, att_file)
                else:
                    latest_file = ''
            return 'poc', latest_file
        return '', ''

    def wait_for_file_download(self):
        try:
            com.wait_element(self.browser, '//iframe')
            self.browser.driver.switch_to.frame(self.browser.find_element('//iframe'))
            com.take_screenshot(self.browser, 'pacer_download_file_2')
            self.browser.click_element_when_visible('//button')
        except:
            pass
        while True:
            time.sleep(5)
            list_of_files = glob.glob(self.path_to_temp + '\*')
            latest_file = max(list_of_files, key=os.path.getctime)
            print(latest_file)
            if 'crdownload' not in latest_file:
                break
        return latest_file

    def merge_poc_document(self, main_file, att_file):
        pdfs = []
        final_pdf_path = os.path.join(os.path.abspath(os.path.dirname(main_file)), 'poc_merged.pdf')
        merger = PdfFileMerger()
        pdfs.append(main_file)
        pdfs.append(att_file)
        for pdf in pdfs:
            merger.append(pdf)
        merger.write(final_pdf_path)
        merger.close()
        return final_pdf_path
