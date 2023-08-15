import datetime
import os
import shutil
from traceback import print_exc

from RPA.Robocloud.Items import Items
from RPA.Robocloud.Secrets import Secrets
from ta_bitwarden_cli.ta_bitwarden_cli import Bitwarden

from libraries.central_reach import CentralReach
from libraries.common import log_message, print_version
from libraries.gmail_service import Gmail
from libraries.utils import ScheduledMaintenanceException

CREDENTIALS_NAME = {
    'central reach': 'Behavioral Healthworks Central Reach',
}
REPORT_RECIPIENT = 'aperez@behavioralhealthworks.com'


def get_input() -> (str, str, str):
    library = Items()
    library.load_work_item_from_environment()
    id_numbers: str = str(library.get_work_item_variable('id_numbers')).strip()
    start_date: str = library.get_work_item_variable('start_date')
    end_date: str = library.get_work_item_variable('end_date')

    log_message(f'Received input data: "{id_numbers}"; "{start_date}"; "{end_date}"')
    return id_numbers, start_date, end_date


def get_bitwarden_credentials(credentials_name: str = 'bitwarden_credentials') -> dict:
    secrets = Secrets()
    bitwarden_credentials = secrets.get_secret(credentials_name)

    return bitwarden_credentials


def main():
    log_message("Start Behavioral Health Works - Orphan Payments")
    print_version()

    # Get credentials
    bitwarden_credentials = get_bitwarden_credentials()
    bw = Bitwarden(bitwarden_credentials)
    CREDENTIALS = bw.get_credentials(CREDENTIALS_NAME)
    # Get inputs
    payments_ids_str, start_date_str, end_date_str = get_input()
    start_date = datetime.datetime.strptime(start_date_str, '%m/%d/%Y')
    end_date = datetime.datetime.strptime(end_date_str, '%m/%d/%Y')
    input_payments_ids = list(map(int, payments_ids_str.split(',')))

    path_to_output = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output')
    if os.path.exists(path_to_output):
        shutil.rmtree(path_to_output)
    os.makedirs(path_to_output)

    # Login to CentralReach
    log_message('Login to Central Reach')
    cr = CentralReach(CREDENTIALS['central reach'])

    #  Navigate to ERA List & Find Claim/Check to Process
    log_message(f'Navigate to Era List for checking {len(input_payments_ids)} payment IDs')
    payments_ids = cr.initial_payment_ids_check(input_payments_ids, start_date, end_date)
    log_message(f'{len(payments_ids)} payment IDs will be processed')

    if payments_ids:
        try:
            cr.process_payments_ids(payments_ids)
        except ScheduledMaintenanceException:
            pass
        except Exception as ex:
            print_exc()
            log_message(f"An error occurred while process payments\n{str(ex)}", 'ERROR')
            # Verify Complete Reconciliation of Payments
            cr.check_payment_ids_reconciled_status(payments_ids, start_date, end_date)
        else:
            # Verify Complete Reconciliation of Payments
            cr.check_payment_ids_reconciled_status(payments_ids, start_date, end_date)

    html_body = cr.report.get_report_in_html()

    if html_body:
        try:
            gmail = Gmail()
            gmail.send_message(to=REPORT_RECIPIENT,
                               subject='Orphan Payments Bot: manual check',
                               html_body=html_body,
                               attachments=(os.path.abspath('libraries/mail/images/ta.jpg'),
                                            os.path.abspath('libraries/mail/images/emj.jpg')))
            log_message(f'Sent report to {REPORT_RECIPIENT}')
        except Exception as ex:
            log_message(f"An error occurred while sending the letter, the body of the letter will be saved in outputs\n"
                        f"{str(ex)}", 'ERROR')
            with open(os.path.join(path_to_output, 'unsent_letter.html'), "w", encoding="utf-8") as f:
                f.write(html_body)
    else:
        log_message('Nothing to report')
    log_message("End Behavioral Health Works - Orphan Payments")


if __name__ == '__main__':
    main()
