import os
import traceback
from datetime import datetime
from RPA.Robocloud.Secrets import Secrets
from libraries import common as com
from libraries import bitwarden
from libraries.web_tempo import Tempo
from libraries.web_caseaware import CaseAware
from libraries.web_pacer import Pacer
from libraries.parse_pdf_docs import ParsePDFDOcs

ENV = ''
CREDS = {
    'tempo': 'RSMA - Tempo-CMS',
    'pacer': 'RSMA - Pacer Case Locator',
    'caseaware': 'RSMA - Caseaware',
    'outlook': "TA's RSMA Outlook Account"
}

SAFE_NETS = False


def main():
    ENV = com.get_env()
    bot_creds = get_all_credentials(ENV)
    try:
        com.win32_cache_cleanup()
    except:
        pass
    com.log_message('Start RSMA1 - BK New Case Entry Bot')
    com.print_version()
    com.log_message('Starting Tempo', 'TRACE')
    tempo_object = Tempo(bot_creds['tempo'])
    pacer_obj = Pacer(bot_creds['pacer'])
    ca_object = CaseAware(bot_creds['caseaware'], bot_creds['outlook'], SAFE_NETS)

    tempo_object.open_login()
    if tempo_object.is_site_available:
        tempo_object.get_worklist_queue()
        tempo_object.close_logout()
    if tempo_object.is_failed:
        com.log_message(tempo_object.error_message, 'ERROR')
        exit(1)

    for loan_item in tempo_object.loans:
        if loan_item['can_be_processed']:
            try:
                com.log_message('Starting Pacer for ' + loan_item['loan_number'], 'TRACE')

                pacer_obj.login_to_pacer()
                case_found = pacer_obj.search_case(loan_item['case_number'], loan_item['parties'], loan_item['district'])
                if not case_found:
                    loan_item['gen_supplemental_step'] = True
                    continue
                claim_no = pacer_obj.get_claim_no_by_creditor('carrington mortgage')  # services
                loan_item['pacer_data'] = pacer_obj.parsed_data
                if claim_no == '-1':
                    com.log_message('Court Claim Number not Identified, trying "vest in the name of"')
                    claim_no = pacer_obj.get_claim_no_by_creditor(
                        ' '.join(loan_item['vest_in_the_name_of'].split(' ')[:3]).lower())
                loan_item['gen_supplemental_step'] = False
                if claim_no == '-1':
                    loan_item['gen_supplemental_step'] = True
                    com.log_message('Court Claim Number not Identified, executing supplemental step')
                else:
                    com.log_message('Court Claim Number Identified')
                    loan_item['claim_no'] = claim_no
                    loan_item['doc_type'].append(pacer_obj.get_doc_type_to_use(claim_no))
                    com.log_message('Documents to use: ' + loan_item['doc_type'][0] + ', ' + loan_item['doc_type'][1], 'TRACE')
                    file_type, file_path = pacer_obj.download_file_by_claim_number_and_date(claim_no, loan_item['files'],
                                                                                            loan_item['doc_type'])
                    if file_type != '':
                        if file_type == 'nopc':
                            new_filepath = os.path.join(loan_item['path_to_folder'], os.path.basename(file_path))
                            os.rename(file_path, new_filepath)
                            loan_item['files']['nopc']['path'] = new_filepath
                            loan_item['files']['nopc']['downloaded'] = True
                        elif file_type == 'poc':
                            new_filepath = os.path.join(loan_item['path_to_folder'], os.path.basename(file_path))
                            os.rename(file_path, new_filepath)
                            loan_item['files']['poc']['path'] = new_filepath
                            loan_item['files']['poc']['downloaded'] = True
            except Exception as ex:
                com.log_message('Error in pacer flow: ' + str(ex), 'ERROR')
                traceback.print_exc()
                pacer_obj.browser.capture_page_screenshot(
                    os.path.join(os.environ.get(
                        "ROBOT_ROOT", os.getcwd()),
                        'output',
                        f'Error in pacer {loan_item["loan_number"]} - {datetime.now().strftime("%H_%M_%S")}.png')
                )
            try:
                loan_item['files']['pacer'] = {}
                loan_item['files']['claims'] = {}
                new_filepath_pdf = os.path.join(loan_item['path_to_folder'], os.path.basename(pacer_obj.path_to_pdf))
                new_filepath_html = os.path.join(loan_item['path_to_folder'], os.path.basename(pacer_obj.path_to_html))
                os.rename(pacer_obj.path_to_pdf, new_filepath_pdf)
                os.rename(pacer_obj.path_to_html, new_filepath_html)
                loan_item['files']['pacer']['path'] = new_filepath_pdf
                new_filepath_cl_pdf = os.path.join(loan_item['path_to_folder'], os.path.basename(pacer_obj.path_to_claims_pdf))
                new_filepath_cl_html = os.path.join(loan_item['path_to_folder'], os.path.basename(pacer_obj.path_to_claims))
                os.rename(pacer_obj.path_to_claims_pdf, new_filepath_cl_pdf)
                os.rename(pacer_obj.path_to_claims, new_filepath_cl_html)
                loan_item['files']['claims']['path'] = new_filepath_cl_pdf
                try:
                    os.remove(pacer_obj.path_to_html)
                    os.remove(pacer_obj.path_to_claims)
                except:
                    pass
            except Exception as ex:
                com.log_message('Failed to move pacer files', 'TRACE')
                com.log_message(ex, 'TRACE')
                traceback.print_exc()
    ca_object.browser.close_all_browsers()
    for loan_item in tempo_object.loans:
        if loan_item['can_be_processed']:
            print('==================================')
            try:
                com.log_message(f'Starting CaseAware for {loan_item["loan_number"]}', 'TRACE')
                ca_object.open_login()
                try:
                    ParsePDFDOcs.parse_docs(loan_item)
                except:
                    loan_item['gen_supplemental_step'] = True
                com.log_message(loan_item, 'TRACE')
                ca_object.process_loan(loan_item)
                if ca_object.is_failed:
                    com.log_message(ca_object.error_message, 'ERROR')
                    exit(1)
            except Exception as e:
                com.log_message('Error in CA flow: ' + str(e), 'ERROR')
                traceback.print_exc()
                ca_object.browser.capture_page_screenshot(
                    os.path.join(os.environ.get(
                        "ROBOT_ROOT", os.getcwd()),
                        'output',
                        f'Error in CA {loan_item["loan_number"]} - {datetime.now().strftime("%H_%M_%S")}.png')
                )
            finally:
                ca_object.close_logout()
                ca_object.browser.close_all_browsers()

    tempo_object.open_login()
    for loan_item in tempo_object.loans:
        if 'close_1448' not in loan_item:
            com.log_message(loan_item['loan_number'] + ' skipping close_1448', 'TRACE')
            continue
        else:
            if loan_item['close_1448']:
                com.log_message(loan_item['loan_number'] + ' closing 1448', 'TRACE')
                tempo_object.close_task_1448(loan_item['loan_number'])
            else:
                com.log_message(loan_item['loan_number'] + ' skipping close_1448', 'TRACE')
                continue
    tempo_object.close_logout()

    com.log_message('100% task - Bot has completed its task')
    com.log_message('End RSMA1 - BK New Case Entry Bot')


def get_all_credentials(env: str, credentials_name: str = 'bitwarden_credentials'):
    secrets = Secrets()
    bitwarden_credentials = secrets.get_secret(credentials_name)
    bw = bitwarden.Bitwarden(bitwarden_credentials)
    return bw.get_credentials(com.generate_creds(env, CREDS))


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        com.log_message('Error in main flow: ' + str(ex), 'ERROR')
        traceback.print_exc()
