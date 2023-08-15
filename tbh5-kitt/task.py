import os
import traceback
import sys
import datetime

from RPA.Robocloud.Items import Items
from RPA.Robocloud.Secrets import Secrets
from libraries import common
from libraries.google_drive import GoogleDrive
from ta_bitwarden_cli.ta_bitwarden_cli import Bitwarden
from libraries.central_reach import CentralReach
from libraries.waystar import WayStar
from libraries.excel import ExcelInterface


CREDENTIALS_NAME = {
    'central reach': 'TBH Central Reach Login',
    'waystar': 'Waystar Login'
}
CREDENTIALS = {
    'example': {'login': '', 'password': '', 'url': '', 'otp': ''}
}


def get_bitwarden_credentials(credentials_name: str = 'bitwarden_credentials') -> dict:
    secrets = Secrets()
    bitwarden_credentials = secrets.get_secret(credentials_name)

    return bitwarden_credentials


def main():
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp'))
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output'))
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'output')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'output'))

    common.initialize_google_logger(
        'TBH5 - KITT Output',
        f'KITT | {datetime.datetime.utcnow().strftime("%m/%d/%Y")} | {datetime.datetime.utcnow().strftime("%m/%d/%Y %I:%M %p")}'
    )

    common.log_message('Start Trumpet Behavioral Health - KITT')
    common.print_version()

    # get credentials
    bitwarden_credentials = get_bitwarden_credentials()

    global CREDENTIALS
    global CREDENTIALS_NAME
    bw = Bitwarden(bitwarden_credentials)
    CREDENTIALS = bw.get_credentials(CREDENTIALS_NAME)

    drive = GoogleDrive()

    # Download and parse Current Month Cash Disbursement.xlsx
    drive.download_file_by_name('Cash Receipts.xlsx')
    cash_receipts = ExcelInterface(drive.path_to_file)

    drive.download_file_by_name('Other- LOCKBOX REMITS.xlsx')
    lockbox_remit_other: ExcelInterface = ExcelInterface(drive.path_to_file)

    common.log_message('5% field - Logging In')
    ws = WayStar(CREDENTIALS['waystar'])
    if not ws.is_site_available:
        common.log_message('WayStar site is not available', 'ERROR')
        exit(1)

    cr = CentralReach(CREDENTIALS['central reach'])
    if not cr.is_site_available:
        common.log_message('CentralReach site is not available', 'ERROR')
        exit(1)
    cr.waystar = ws
    cr.cash_receipts = cash_receipts
    cr.lockbox_remit_other = lockbox_remit_other

    cr.cash_receipts.read_current_month_cash_disbursement()
    while cr.cash_receipts.current_valid_sheet:
        cr.start_date = cr.cash_receipts.current_valid_date
        cr.end_date = cr.cash_receipts.current_valid_date
        common.log_message(f'Start processing {cr.cash_receipts.current_valid_sheet} sheet')

        cr.payments_processing()
        cr.cash_receipts.read_current_month_cash_disbursement()
    drive.upload_file(cr.cash_receipts.file_path)
    cr.reconcile_zero_payments_and_denials()

    common.log_message('100% field - Processes Complete')
    common.log_message('End Trumpet Behavioral Health - KITT')
    common.google_logger.send_all_logs()


if __name__ == '__main__':
    main()
