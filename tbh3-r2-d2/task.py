import os
import datetime

from RPA.Robocloud.Items import Items
from RPA.Robocloud.Secrets import Secrets
from libraries import google_drive, common
from libraries.central_reach import CentralReach
from libraries.waystar import WayStar
from libraries.excel import ExcelInterface
from ta_bitwarden_cli.ta_bitwarden_cli import Bitwarden


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


def get_input() -> (str, str, str):
    library = Items()
    library.load_work_item_from_environment()
    insurance_name: str = str(library.get_work_item_variable('insurance_name')).strip()
    start_date: str = library.get_work_item_variable('start_date')
    end_date: str = library.get_work_item_variable('end_date')

    return insurance_name, start_date, end_date


def main():
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp'))
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output'))
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'output')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'output'))

    insurance_name, start_date, end_date = get_input()
    common.initialize_google_logger(
        'TBH3 - R2-D2 Output',
        f'R2D2 | {insurance_name} {start_date} - {end_date} | {datetime.datetime.utcnow().strftime("%m/%d/%Y %I:%M %p")}'
    )

    common.log_message('Start Trumpet Behavioral Health - R2-D2')
    common.print_version()
    common.log_message(f'Received input data: {insurance_name}, {start_date}, {end_date}')

    # get credentials
    bitwarden_credentials = get_bitwarden_credentials()

    global CREDENTIALS
    global CREDENTIALS_NAME
    bw = Bitwarden(bitwarden_credentials)
    CREDENTIALS = bw.get_credentials(CREDENTIALS_NAME)

    drive = google_drive.GoogleDrive()

    # Download and parse TBH Payor Info.xlsx
    drive.download_file_by_name('TBH Payor Info.xlsx')
    payor_mapping = ExcelInterface(drive.path_to_file)
    payor_mapping.read_mapping_file()

    common.log_message('5% field - Logging In')
    ws = WayStar(CREDENTIALS['waystar'])
    if not ws.is_site_available:
        common.log_message('WayStar site is not available', 'ERROR')
        exit(1)

    cr = CentralReach(CREDENTIALS['central reach'])
    cr.waystar = ws
    if not cr.is_site_available:
        common.log_message('CentralReach site is not available', 'ERROR')
        exit(1)

    cr.mapping = payor_mapping
    cr.start_date = datetime.datetime.strptime(start_date, '%m/%d/%Y')
    cr.end_date = datetime.datetime.strptime(end_date, '%m/%d/%Y')
    # cr.start_date = datetime.datetime.strptime('11/1/2020', '%m/%d/%Y')
    # cr.end_date = datetime.datetime.strptime('02/28/2021', '%m/%d/%Y')
    common.log_message('Start date: {}. End date: {}'.format(cr.start_date.strftime('%Y-%m-%d'), cr.end_date.strftime('%Y-%m-%d')))
    cr.apply_patient_responsibility(insurance_name)

    common.log_message('100% field - Processes Complete')
    common.log_message('End Trumpet Behavioral Health - R2-D2')
    common.google_logger.send_all_logs()


if __name__ == '__main__':
    main()
