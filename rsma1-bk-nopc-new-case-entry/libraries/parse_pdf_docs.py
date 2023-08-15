import os
import re
import traceback

from RPA.PDF import PDF
from libraries.ocr_pdf import OcrPdf
import libraries.common as com

# 1,000.89; 987.60; 100
AMOUNT_PATTERN = '(?!.*[\+\.\,]{2}.*)\d[\d\.\,\ ]*\d'

# 12/31/20
DATE_PATTERN = '[0-3]?[0-9]/[0-3]?[0-9]/(?:[0-9]{2})?[0-9]{2}'

# none or multiple spaces
SPACES_PATTERN = '[ ]{0,}'


class ParsePDFDOcs:
    @staticmethod
    def parse_docs(loan_data):
        is_failed_parsing = False
        try:
            if 'nopc' in loan_data['doc_type'] and loan_data['files']['nopc']['downloaded']:
                com.log_message('Parsing NOPC file', 'TRACE')
                loan_data['files']['nopc']['data'] = ParsePDFDOcs.notice_of_payment_change(
                    loan_data['files']['nopc']['path'])
            elif 'poc' in loan_data['doc_type'] and loan_data['files']['poc']['downloaded']:
                com.log_message('Parsing POC file', 'TRACE')
                loan_data['files']['poc']['data'] = ParsePDFDOcs.proof_of_claim(loan_data['files']['poc']['path'])
        except Exception as ex:
            com.log_message('Failed to parse NOPC/POC file', 'TRACE')
            com.log_message(ex, 'TRACE')
            traceback.print_exc()
            is_failed_parsing = True
        try:
            if 'escrow' in loan_data['doc_type']:
                com.log_message('Parsing ESCROW file', 'TRACE')
                loan_data['files']['escrow']['data'] = ParsePDFDOcs.escrow_analysis(
                    loan_data['files']['escrow']['path'])
            elif 'arm' in loan_data['doc_type']:
                com.log_message('Parsing ARM file', 'TRACE')
                loan_data['files']['arm']['data'] = ParsePDFDOcs.arm_change(loan_data['files']['arm']['path'])
        except Exception as ex:
            com.log_message('Failed to parse NOPC/POC file', 'TRACE')
            com.log_message(ex, 'TRACE')
            traceback.print_exc()
            is_failed_parsing = True
        if is_failed_parsing:
            raise Exception('Failed to parse one of files')

    @staticmethod
    def escrow_analysis(path_to_escrow_analysis):
        try:
            parsed_data = {}
            ocr = OcrPdf(path_to_escrow_analysis)
            ocr.prepare_pdf()
            # current escrow_payment and new escrow_payment
            escrow_payment_values = ParsePDFDOcs.remove_str_empty_items(ocr.find_text_by_re(fr"ESCROW PAYMENT{SPACES_PATTERN}{AMOUNT_PATTERN}"))

            parsed_data['current escrow payment'] = escrow_payment_values[0].replace("ESCROW PAYMENT", "").replace('\x00', ' ').replace(',', '').replace(' ', '').strip()
            parsed_data['new escrow payment'] = escrow_payment_values[1].replace("ESCROW PAYMENT", "").replace('\x00', ' ').replace(',', '').strip()

            # new total payment and  due date
            payment_due_value = ParsePDFDOcs.remove_str_empty_items(ocr.find_text_by_re(fr"BORROWER PAYMENT STARTING WITH THE PAYMENT DUE{SPACES_PATTERN}{DATE_PATTERN}{SPACES_PATTERN}==>{SPACES_PATTERN}{AMOUNT_PATTERN}", 2))[0]
            parsed_data['due date'] = re.findall(DATE_PATTERN, payment_due_value)[0].replace('\x00', ' ').replace(',', '').strip()
            parsed_data["new total payment"] = re.findall(AMOUNT_PATTERN, payment_due_value)[3].replace('\x00', ' ').replace(',', '').strip()

            try:
                shortage_pymt_values = ocr.find_text_by_re(r"SHORTAGE PYMT[ ]{0,}(?!.*[\+\.\,]{2}.*)\d[\d\.\,]*\d", 1)
                parsed_data['shortage_pymt_curr'] = shortage_pymt_values[0].replace("SHORTAGE PYMT", "").replace('\x00', ' ').replace(',', '').strip()
                com.log_message("SHORTAGE PYMT CURR - " + parsed_data['shortage_pymt_curr'], 'TRACE')
            except Exception as ex:
                com.log_message("NO CURR SHORTAGE PYMT FIELD. " + str(ex), 'TRACE')
                parsed_data['shortage_pymt_curr'] = '0'

            try:
                shortage_pymt_values = ocr.find_text_by_re(r"SHORTAGE PYMT[ ]{0,}(?!.*[\+\.\,]{2}.*)\d[\d\.\,]*\d", 2)
                parsed_data['shortage_pymt_new'] = shortage_pymt_values[0].replace("SHORTAGE PYMT", "").replace('\x00', ' ').replace(',', '').strip()
                com.log_message("SHORTAGE PYMT NEW - " + parsed_data['shortage_pymt_new'], 'TRACE')
            except Exception as ex:
                com.log_message("NO NEW SHORTAGE PYMT FIELD. " + str(ex), 'TRACE')
                parsed_data['shortage_pymt_new'] = '0'

            try:
                shortage_pymt_values = ocr.find_text_by_re(r"(?:SURPLUS REDUCTN|SURPLUS PYMT)[ ]{0,}(?!.*[\+\.\,]{2}.*)\d[\d\.\,]*\d", 1)
                parsed_data['surplus_pymt_curr'] = shortage_pymt_values[0].replace("SURPLUS PYMT", "").replace("SURPLUS REDUCTN", "").replace('\x00', ' ').replace(',', '').strip()
                com.log_message("SURPLUS CURR PYMT - " + parsed_data['surplus_pymt_curr'], 'TRACE')
            except Exception as ex:
                com.log_message("NO CURR SURPLUS PYMT FIELD. " + str(ex), 'TRACE')
                parsed_data['surplus_pymt_curr'] = '0'

            try:
                shortage_pymt_values = ocr.find_text_by_re(
                    r"(?:SURPLUS REDUCTN|SURPLUS PYMT)[ ]{0,}(?!.*[\+\.\,]{2}.*)\d[\d\.\,]*\d", 2)
                parsed_data['surplus_pymt_new'] = shortage_pymt_values[0].replace("SURPLUS PYMT", "").replace(
                    "SURPLUS REDUCTN", "").replace('\x00', ' ').replace(',', '').strip()
                com.log_message("SURPLUS NEW PYMT - " + parsed_data['surplus_pymt_new'], 'TRACE')
            except Exception as ex:
                com.log_message("NO NEW SURPLUS PYMT FIELD. " + str(ex), 'TRACE')
                parsed_data['surplus_pymt_new'] = '0'
            return parsed_data

        except Exception as ex:
            raise Exception(f"Unable to parse data from {os.path.basename(path_to_escrow_analysis)}. " + str(ex))

    @staticmethod
    def arm_change(path_to_arm_change) -> dict:
        try:
            parsed_data = {}
            ocr = OcrPdf(path_to_arm_change)
            ocr.prepare_pdf()
            all_strings = ocr.find_text_by_re(r".*[\S]")

            for i in range(len(all_strings)):
                str_item: str = all_strings[i].lower().replace('\x00', ' ').strip()
                if 'mortgage' in str_item or 'change' in str_item:
                    continue
                if 'interest rate' in str_item and 'current interest rate' not in parsed_data:
                    values = str_item.replace('interest rate', 'interestrate').strip().split(' ')
                    if len(values) > 2:
                        value_curr = values[1].replace('/', '7').replace('1.', '7.').strip()
                        value_new = values[2].replace('/', '7').replace('1.', '7.').strip()
                    else:
                        value_curr = all_strings[i + 1].lower().replace('\x00', ' ').replace('/', '7').replace('1.',
                                                                                                               '7.').strip()
                        value_new = all_strings[i + 2].lower().replace('\x00', ' ').replace('/', '7').replace('1.',
                                                                                                              '7.').strip()
                    m_value_curr = re.match('[\d\.\,\%]*', value_curr)
                    m_value_new = re.match('[\d\.\,\%]*', value_new)
                    if m_value_curr is not None and m_value_new is not None:
                        parsed_data['current interest rate'] = value_curr.replace("%", "").strip()
                        parsed_data['new interest rate'] = value_new.replace("%", "").strip()
                    else:
                        continue

                elif 'principal' in str_item and 'current principal' not in parsed_data:
                    values = str_item.split(' ')
                    if len(values) > 1:
                        value_curr = values[1].replace("$", "").replace(',', '').strip()
                        value_new = values[2].replace("$", "").replace(',', '').strip()
                    else:
                        value_curr = all_strings[i + 1].lower().replace('\x00', ' ').strip()
                        value_new = all_strings[i + 2].lower().replace('\x00', ' ').strip()
                    m_value_curr = re.match('[\d\.\,\$]*', value_curr)
                    m_value_new = re.match('[\d\.\,\$]*', value_new)
                    if m_value_curr is not None and m_value_new is not None:
                        parsed_data['current principal'] = value_curr.replace("$", "").replace(',', '').strip()
                        parsed_data['new principal'] = value_new.replace("$", "").replace(',', '').strip()
                    else:
                        continue

                elif 'interest' in str_item and 'current interest' not in parsed_data:
                    values = str_item.split(' ')
                    if len(values) > 2:
                        value_curr = values[1].replace("$", "").replace(',', '').strip()
                        value_new = values[2].replace("$", "").replace(',', '').strip()
                    else:
                        value_curr = all_strings[i + 1].lower().replace('\x00', ' ').strip()
                        value_new = all_strings[i + 2].lower().replace('\x00', ' ').strip()
                    m_value_curr = re.match('[\d\.\,\$]*', value_curr)
                    m_value_new = re.match('[\d\.\,\$]*', value_new)
                    if m_value_curr is not None and m_value_new is not None:
                        parsed_data['current interest'] = value_curr.replace("$", "").replace(',', '').strip()
                        parsed_data['new interest'] = value_new.replace("$", "").replace(',', '').strip()
                    else:
                        continue

                elif 'total (monthly)' in str_item:
                    try:
                        parsed_data['due date'] = str(
                            re.findall(pattern=r"[0-3]?[0-9]/[0-3]?[0-9]/(?:[0-9]{2})?[0-9]{2}", string=str_item)[
                                0]).strip()
                        com.log_message('str item: ' + str_item, 'TRACE')
                        values = re.findall(pattern=AMOUNT_PATTERN, string=str_item)
                        com.log_message('values found: ' + str(values), 'TRACE')
                        if len(values) < 2:
                            parsed_data['new total'] = values[0].replace("$", "").replace(',', '').strip()
                        else:
                            parsed_data['new total'] = values[1].replace("$", "").replace(',', '').strip()
                        # value_new = str_item.split(' ')[0].replace("$", "").replace(',', '').strip()
                        # parsed_data['new total'] = value_new.replace("$", "").replace(',', '').strip()
                    except:
                        str_item = all_strings[i + 3].lower().replace('\x00', ' ').strip()
                        parsed_data['due date'] = str(
                            re.findall(pattern=r"[0-3]?[0-9]/[0-3]?[0-9]/(?:[0-9]{2})?[0-9]{2}", string=str_item)[
                                0]).strip()
                        value_new = str_item.split(' ')[0].replace("$", "").replace(',', '').strip()
                        parsed_data['new total'] = value_new.replace("$", "").replace(',', '').strip()

            com.log_message("Interest rate curr - " + parsed_data['current interest rate'], 'TRACE')
            com.log_message("Interest rate new - " + parsed_data['new interest rate'], 'TRACE')
            com.log_message("Principal payment curr - " + parsed_data['current principal'], 'TRACE')
            com.log_message("Principal payment new - " + parsed_data['new principal'], 'TRACE')
            com.log_message("Interest payment curr - " + parsed_data['current interest'], 'TRACE')
            com.log_message("Interest payment new - " + parsed_data['new interest'], 'TRACE')
            com.log_message("Due Date - " + parsed_data['due date'], 'TRACE')
            com.log_message("New total - " + parsed_data['new total'], 'TRACE')
            return parsed_data
        except Exception as ex:
            raise Exception(f"Unable to parse data from {os.path.basename(path_to_arm_change)}. " + str(ex))

    @staticmethod
    def notice_of_payment_change(path_to_nopc):
        pdf_reader = PDF()
        new_escrow_payment = ''
        new_total_payment = ''
        pdf_reader.get_text_from_pdf(path_to_nopc)
        page = pdf_reader.active_pdf_document.pages[1]

        for line in range(len(page.content)):
            current_line_text = ''
            try:
                current_line_text = str(page.content[line].text).replace('\x00', ' ')
            except:
                continue

            try:
                if current_line_text.find("New escrow payment") != -1:
                    if current_line_text.find("$") != -1:
                        new_escrow_payment = current_line_text.replace("New escrow payment:", "").replace("$", "").replace('\x00', ' ').replace(',', '').strip()
                    else:
                        new_escrow_payment = str(page.content[line + 1].text).replace("$", "").replace('\x00', ' ').replace(',', '').strip()
                elif current_line_text.find("Newescrowpayment") != -1:
                    if current_line_text.find("$") != -1:
                        new_escrow_payment = current_line_text.replace("Newescrowpayment:", "").replace("$", "").replace('\x00', ' ').replace(',', '').strip()
                    else:
                        new_escrow_payment = str(page.content[line + 1].text).replace("$", "").replace('\x00', ' ').replace(',', '').strip()
            except Exception as ex:
                com.log_message(repr(page.content[line].text), 'TRACE')
                com.log_message(str(ex), 'TRACE')
                com.log_message(line, 'TRACE')

            try:
                if current_line_text.find("New total payment") != -1:
                    if current_line_text.find("$") != -1:
                        new_total_payment = current_line_text.replace("New total payment:", "").replace("$", "").replace('\x00', ' ').replace(',', '').strip()
                    else:
                        new_total_payment = str(page.content[line + 1].text).replace("$", "").replace('\x00', ' ').replace(',', '').strip()
                elif current_line_text.find("Newtotalpayment") != -1:
                    if current_line_text.find("$") != -1:
                        new_total_payment = current_line_text.replace("Newtotalpayment:", "").replace("$", "").replace('\x00', ' ').replace(',', '').strip()
                    else:
                        new_total_payment = str(page.content[line + 1].text).replace("$", "").replace('\x00', ' ').replace(',', '').strip()
            except Exception as ex:
                com.log_message(repr(page.content[line].text), 'TRACE')
                com.log_message(str(ex), 'TRACE')
                com.log_message(line, 'TRACE')
        pdf_reader.close_all_pdfs()
        if new_escrow_payment.replace('_', '').strip() == '':
            new_escrow_payment = '0.00'
        if new_total_payment.replace('_', '').strip() == '':
            new_total_payment = '0.00'
        com.log_message("New Escrow Payment: " + new_escrow_payment, 'TRACE')
        com.log_message("New Total Payment: " + new_total_payment, 'TRACE')
        if new_escrow_payment == '0.00' and new_total_payment == '0.00':
            new_escrow_payment, new_total_payment = ParsePDFDOcs.notice_of_payment_change_ocr(path_to_nopc)
        return {'new_escrow_payment': new_escrow_payment, 'new_total_payment': new_total_payment}

    @staticmethod
    def proof_of_claim(path_to_poc):
        monthly_escrow = ''
        principal_and_interest = ''
        repl_char = {':', ';', '$'}
        ocr = OcrPdf(path_to_poc)
        ocr.prepare_special_page()
        monthly_escrow_values = ocr.find_text_by_re(
            r"[M|m]onthly [E|e]scrow[:.,;]{0,}[ ]{0,}\$*(?!.*[\+\.\,]{2}.*)\d[\d\.\,]*\d", 4)
        principal_and_interest_values = ocr.find_text_by_re(
            r"[P|p]rincipal &[ \n]*[I|i]nterest[:.,;]{0,}[ ]{0,}\$*(?!.*[\+\.\,]{2}.*)\d[\d\.\,]*\d", 4)

        for index_1 in range(len(monthly_escrow_values)):
            if monthly_escrow_values[index_1].lower().find("monthly escrow") != -1:
                tmp_text = monthly_escrow_values[index_1].lower().replace("monthly escrow", "").split(' ')[1]
                monthly_escrow = ''.join([c for c in tmp_text if c not in repl_char]).replace('\x00', ' ').replace(',', '').strip()
                break
        for index_2 in range(len(principal_and_interest_values)):
            if principal_and_interest_values[index_2].lower().replace("\n", ' ').find("principal & interest") != -1:
                tmp_text = principal_and_interest_values[index_2].lower().replace("\n", ' ').replace("principal & interest", "").split(' ')[1]
                principal_and_interest = ''.join([c for c in tmp_text if c not in repl_char]).replace('\x00', ' ').replace(',', '').strip()
                break
        com.log_message("Monthly escrow: " + monthly_escrow, 'TRACE')
        com.log_message("Principal & Interest: " + principal_and_interest, 'TRACE')
        return {'monthly_escrow': monthly_escrow, 'principal_and_interest': principal_and_interest}

    @staticmethod
    def remove_str_empty_items(collection):
        new_list = list()
        for index in range(len(collection)):
            if len(collection[index]) == 0:
                continue

            item: str = collection[index].strip()
            if item == '':
                continue

            new_list.append(item)

        return new_list

    @staticmethod
    def get_list_strings_from_pdf(path_to_file):
        pdf_lines = list()
        pdf_reader = PDF()
        pdf_reader.parse_pdf(path_to_file)
        pages = pdf_reader.rpa_pdf_document.pages
        for page in pages:
            for temp in pages[page].content:
                true_content = pages[page].content[temp]
                try:
                    text_line = true_content.text.strip()
                    pdf_lines.append(text_line)
                except:
                    continue
        return pdf_lines

    @staticmethod
    def check_is_correct_pdf(path_to_file: str, check_string: str):
        is_correct = False
        pdf_reader = PDF()
        pages = pdf_reader.get_text_from_pdf(path_to_file)
        for inx_page in pages.keys():
            if check_string.lower().strip() in pages[inx_page].lower():
                is_correct = True
                break
        return is_correct

    @staticmethod
    def notice_of_payment_change_ocr(path_to_nopc):
        new_escrow_payment = ''
        new_total_payment = ''
        repl_char = {':', ';', '$', '§', ' '}
        ocr = OcrPdf(path_to_nopc)
        ocr.prepare_amount_of_pages(1)
        new_total_payment_values = ocr.find_text_by_re(
            r"[N|n]ew [T|t]otal [P|p]ayment\D*\s*[$§]{0,}\s*(?!.*[\+\.\,\ ]{2}.*)\d[\d\.\,\ ]*\d", 1)
        new_escrow_payment_values = ocr.find_text_by_re(
            r"[N|n]ew [E|e]scrow [P|p]ayment\D*\s*[$§]{0,}\s*(?!.*[\+\.\,\ ]{2}.*)\d[\d\.\,\ ]*\d", 1)
        if len(new_escrow_payment_values) < 1:
            new_escrow_payment_values = ocr.find_text_by_re(
                r"[C|c]urrent [E|e]scrow [P|p]ayment.*(?!.*[\+\.\, ]{2}.*)\d[\d\.\, ]*\d", 1)

        for index_1 in range(len(new_total_payment_values)):
            if new_total_payment_values[index_1].lower().find("new total payment") != -1:
                tmp_text = new_total_payment_values[index_1].lower().replace("new total payment", "")
                new_total_payment = ''.join([c for c in tmp_text if c not in repl_char]).replace('\x00', ' ').replace(
                    ',', '').strip()
                break
        for index_2 in range(len(new_escrow_payment_values)):
            if new_escrow_payment_values[index_2].lower().find("new escrow payment") != -1:
                tmp_text = new_escrow_payment_values[index_2].lower().replace("new escrow payment", "")
                new_escrow_payment = ''.join([c for c in tmp_text if c not in repl_char]).replace('\x00', ' ').replace(
                    ',', '').strip()
                break
            elif new_escrow_payment_values[index_2].lower().find("current escrow payment") != -1:
                tmp_text = new_escrow_payment_values[index_2].lower().replace("current escrow payment", "").split('$')[
                    -1]
                new_escrow_payment = ''.join([c for c in tmp_text if c not in repl_char]).replace('\x00', ' ').replace(
                    ',', '').strip()
                break

        new_total_payment = re.sub('[a-zA-Z]+', '', new_total_payment)
        new_escrow_payment = re.sub('[a-zA-Z]+', '', new_escrow_payment)
        if new_escrow_payment == '':
            new_escrow_payment = '0.00'
        if new_total_payment == '':
            new_total_payment = '0.00'
        com.log_message("New Escrow Payment: " + new_escrow_payment, 'TRACE')
        com.log_message("New Total Payment: " + new_total_payment, 'TRACE')
        return [new_escrow_payment, new_total_payment]

    @staticmethod
    def poc_case_number_parse(path_to_poc):
        case_num = ''
        filed_date = ''
        ocr = OcrPdf(path_to_poc)
        ocr.prepare_amount_of_pages(2)
        case_num_values = ocr.find_text_by_re(r'(?:[C|c]ase[\s]*[N|n]umber[\s]*)(.+)', 1)
        filed_date_values = ocr.find_text_by_re(r'(?:[F|f]iled\s*)(\d{2}\/\d{2}\/\d{2,4})', 1)

        if len(case_num_values) > 0:
            case_num = case_num_values[0].replace(' ', '').strip()
        if len(filed_date_values) > 0:
            filed_date = filed_date_values[0].replace(' ', '').strip()
        else:
            filed_date_values = ocr.find_text_by_re(r'(?:[F|f]iled\s*)(\d{2}\/\d{2}\/\d{2,4})', 2)
            if len(filed_date_values) > 0:
                filed_date = filed_date_values[0].replace(' ', '').strip()

        if case_num == '':
            case_num = 'error'
        if filed_date == '':
            filed_date = 'error'
        com.log_message("Case Number: " + case_num, 'TRACE')
        com.log_message("Filed Date: " + filed_date, 'TRACE')
        return [case_num, filed_date]
