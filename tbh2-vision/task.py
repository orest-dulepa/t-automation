from RPA.Robocloud.Items import Items
from RPA.Robocloud.Secrets import Secrets
import os
from libraries import google_drive, common
from libraries.central_reach import CentralReach
from libraries.domo import Domo
from libraries.waystar import WayStar
from libraries.excel import ExcelInterface
import datetime
from ta_bitwarden_cli.ta_bitwarden_cli import Bitwarden


CREDENTIALS_NAME = {
    'domo': 'TBH - Domo Login',
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
    client_name: str = str(library.get_work_item_variable('client_name')).strip()
    start_date: str = library.get_work_item_variable('start_date')
    end_date: str = library.get_work_item_variable('end_date')

    return client_name, start_date, end_date


def main():
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp'))
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output'))
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'output')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'output'))

    client_name, start_date, end_date = get_input()
    common.initialize_google_logger(
        'TBH2 - Vision Output',
        f'Vision {client_name} {start_date} - {end_date} | {datetime.datetime.utcnow().strftime("%m/%d/%Y %I:%M %p")}'
    )

    common.log_message('Start Trumpet Behavioral Health - Vision')
    common.print_version()
    common.log_message(f'Received input data: {client_name}, {start_date}, {end_date}')

    # get credentials
    bitwarden_credentials = get_bitwarden_credentials()

    global CREDENTIALS
    global CREDENTIALS_NAME
    bw = Bitwarden(bitwarden_credentials)
    CREDENTIALS = bw.get_credentials(CREDENTIALS_NAME)

    # Get mapping from DOMO
    domo_mapping_site = {}
    try:
        domo = Domo(CREDENTIALS['domo'])
        if not domo.is_site_available:
            common.log_message('ERROR: DOMO site is not available', 'ERROR')
        else:
            path_to_domo_file = domo.get_bcba_mapping()
            domo_mapping = ExcelInterface(path_to_domo_file)
            domo_mapping_site = domo_mapping.read_domo_mapping()
    except Exception as ex:
        common.log_message(str(ex), 'ERROR')
        common.log_message('ERROR: DOMO site is not available', 'ERROR')

    drive = google_drive.GoogleDrive()

    # Download and parse TBH Payor Info.xlsx
    drive.download_file_by_name('TBH Payor Info.xlsx')
    payor_mapping = ExcelInterface(drive.path_to_file)
    payor_mapping.read_mapping_file()

    # Download and parse Trump Site List.xls
    drive.download_file_by_name('Trump Site List.xlsx')
    trump_site_list = ExcelInterface(drive.path_to_file)

    # Download and parse Current Month DOMO Provider Mapping.xls
    drive.download_file_by_name('Current Month DOMO Provider Mapping.xlsx')
    domo_mapping_file = ExcelInterface(drive.path_to_file)

    common.log_message('5% field - Logging In')
    ws = WayStar(CREDENTIALS['waystar'])
    ws.npi = payor_mapping.npi
    if not ws.is_site_available:
        common.log_message('WayStar site is not available', 'ERROR')
        exit(1)

    cr = CentralReach(CREDENTIALS['central reach'])
    cr.waystar = ws
    if not cr.is_site_available:
        common.log_message('CentralReach site is not available', 'ERROR')
        exit(1)
    drive.download_file_by_name('Crosswalk Guide.xlsx')
    crosswalk_guide = ExcelInterface(drive.path_to_file)
    cr.crosswalk_guide = crosswalk_guide.read_crosswalk_guide()
    cr.waystar.crosswalk_guide = cr.crosswalk_guide

    cr.mapping = payor_mapping
    cr.domo_mapping_file = domo_mapping_file.read_domo_mapping()
    cr.domo_mapping_site = domo_mapping_site
    cr.trump_site_list = trump_site_list.read_trump_site_list()
    cr.open_second_tab()
    cr.open_second_tab()

    cr.start_date = datetime.datetime.strptime(start_date, '%m/%d/%Y')
    cr.end_date = datetime.datetime.strptime(end_date, '%m/%d/%Y')
    # cr.start_date = datetime.datetime.strptime('01/01/2021', '%m/%d/%Y')
    # cr.end_date = datetime.datetime.strptime('2/16/2021', '%m/%d/%Y')
    # client_name = 'Yash Modi'
    common.log_message('Start date: {}. End date: {}'.format(cr.start_date.strftime('%Y-%m-%d'), cr.end_date.strftime('%Y-%m-%d')))

    cr.secondary_claims_processing(client_name)

    common.log_message('100% field - Processes Complete')
    common.log_message('End Trumpet Behavioral Health - Vision')
    common.google_logger.send_all_logs()


if __name__ == '__main__':
    main()
