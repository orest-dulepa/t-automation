import datetime
import os
import shutil
from traceback import print_exc

from RPA.Robocloud.Items import Items
from RPA.Robocloud.Secrets import Secrets
from ta_bitwarden_cli.ta_bitwarden_cli import Bitwarden

from config import (BOT_ACCOUNT, CREDENTIALS_NAME, OUTPUT_FOLDER,
                    REPORT_RECIPIENT, TEMP_FOLDER)
from libraries.central_reach import CentralReach
from libraries.common import log_message, print_version
from libraries.google_services.gmail_service import Gmail
from libraries.report.report_constructor import ReportConstructor
from libraries.utils import ScheduledMaintenanceException


def get_input() -> (str, str):
    library = Items()
    library.load_work_item_from_environment()
    start_date: str = library.get_work_item_variable('start_date')
    end_date: str = library.get_work_item_variable('end_date')

    log_message(f'Received input data: "{start_date}"; "{end_date}"')
    return start_date, end_date


def get_bitwarden_credentials(credentials_name: str = 'bitwarden_credentials') -> dict:
    secrets = Secrets()
    bitwarden_credentials = secrets.get_secret(credentials_name)

    return bitwarden_credentials


def main():
    log_message("Start Behavioral Health Works - Patient Responsibility")
    print_version()

    # Create temp folder
    if os.path.exists(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)
    os.mkdir(TEMP_FOLDER)

    # Get credentials
    bitwarden_credentials = get_bitwarden_credentials()
    bw = Bitwarden(bitwarden_credentials)
    CREDENTIALS = bw.get_credentials(CREDENTIALS_NAME)

    # Get inputs
    start_date_str, end_date_str = get_input()
    start_date = datetime.datetime.strptime(start_date_str, '%m/%d/%Y')
    end_date = datetime.datetime.strptime(end_date_str, '%m/%d/%Y')

    # Login to CentralReach
    log_message('Login to Central Reach')
    cr = CentralReach(CREDENTIALS['central reach'], start_date, end_date)

    try:
        cr.process()
    except ScheduledMaintenanceException:
        cr.warning_messages.append("Work stopped unexpectedly because 'Central Reach' site is currently "
                                   "unavailable due to scheduled maintenance")
    except Exception as ex:
        print_exc()
        log_message(f"An error occurred while process payments\n{str(ex)}", 'ERROR')
        cr.warning_messages.append("Work stopped unexpectedly because there was an unexpected error")

    # Send report
    report: ReportConstructor = cr.make_report()
    try:
        gmail = Gmail(BOT_ACCOUNT)
        gmail.send_message(to=REPORT_RECIPIENT,
                           subject='Patient Responsibility Bot Report',
                           html_body=report.get_html(),
                           attachments=report.attachments)
        log_message(f'Sent report to {REPORT_RECIPIENT}')
    except Exception as ex:
        log_message(f"An error occurred while sending the letter, the body of the letter will be saved in outputs\n"
                    f"{str(ex)}", 'ERROR')
        with open(os.path.join(OUTPUT_FOLDER, 'unsent_letter.html'), "w", encoding="utf-8") as f:
            f.write(report.get_html())
    log_message("End Behavioral Health Works - Patient Responsibility")


if __name__ == '__main__':
    main()
