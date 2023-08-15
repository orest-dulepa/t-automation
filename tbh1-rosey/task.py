from RPA.Robocloud.Items import Items
from RPA.Robocloud.Secrets import Secrets
import os
from libraries import common, google_drive
from libraries.central_reach import CentralReach
from libraries.domo import Domo
from libraries.excel import ExcelInterface
from ta_bitwarden_cli.ta_bitwarden_cli import Bitwarden
import traceback
import sys
import datetime


CREDENTIALS_NAME = {
    "domo": "TBH - Domo Login",
    "central reach": "TBH Central Reach Login",
}
CREDENTIALS = {"example": {"login": "", "password": "", "url": "", "otp": ""}}


def get_bitwarden_credentials(credentials_name: str = "bitwarden_credentials") -> dict:
    secrets = Secrets()
    bitwarden_credentials = secrets.get_secret(credentials_name)

    return bitwarden_credentials


def get_input() -> str:
    library = Items()
    library.load_work_item_from_environment()
    date = library.get_work_item_variable("date")

    if str(date).strip().lower() == "Invalid date".lower():
        date = ""
    return date


def main():
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "output")):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "output"))
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "temp")):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "temp"))
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "temp", "output")):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "temp", "output"))

    date = get_input()
    common.initialize_google_logger(
        'TBH1 - Rosey Output',
        f'Rosey {date} | {datetime.datetime.utcnow().strftime("%m/%d/%Y %I:%M %p")}'
    )

    common.log_message("Start Trumpet Behavioral Health - Rosey")
    common.print_version()
    common.log_message("Received date for processing: {}".format(date))

    # get credentials
    bitwarden_credentials = get_bitwarden_credentials()
    global CREDENTIALS
    global CREDENTIALS_NAME
    bw = Bitwarden(bitwarden_credentials)
    CREDENTIALS = bw.get_credentials(CREDENTIALS_NAME)

    # START TEST
    # date = '03/24/2021'
    # END TEST

    drive = google_drive.GoogleDrive()

    # Download and parse TBH Payor Info.xlsx
    drive.download_file_by_name("TBH Payor Info.xlsx")
    payor_mapping = ExcelInterface(drive.path_to_file)
    payor_mapping.read_mapping_file()

    # Download and parse Current Month DOMO Provider Mapping.xls
    drive.download_file_by_name("Current Month DOMO Provider Mapping.xlsx")
    domo_mapping_file = ExcelInterface(drive.path_to_file)

    # Download and parse Trump Site List.xls
    drive.download_file_by_name("Trump Site List.xlsx")
    trump_site_list = ExcelInterface(drive.path_to_file)

    # Get mapping from DOMO
    domo_mapping_site = {}
    try:
        domo = Domo(CREDENTIALS["domo"])
        if not domo.is_site_available:
            common.log_message("ERROR: DOMO site is not available", "ERROR")
        else:
            path_to_domo_file = domo.get_bcba_mapping()
            domo_mapping = ExcelInterface(path_to_domo_file)
            domo_mapping_site = domo_mapping.read_domo_mapping()
    except Exception as ex:
        common.log_message(str(ex), "ERROR")
        common.log_message("ERROR: DOMO site is not available", "ERROR")

    common.log_message("5% field - Logging In")
    cr = CentralReach(CREDENTIALS["central reach"])
    if not cr.is_site_available:
        common.log_message("CentralReach site is not available", "ERROR")
        exit(1)

    cr.start_date, cr.end_date = cr.calculate_date(date)
    cr.mapping = payor_mapping
    cr.domo_mapping_file = domo_mapping_file.read_domo_mapping()
    cr.domo_mapping_site = domo_mapping_site
    cr.trump_site_list = trump_site_list.read_trump_site_list()

    try:
        common.log_message("45% field - Performing Overlap Check")
        cr.overlap_check()

        common.log_message("50% field - Performing Speech Therapy Process")
        cr.speech_therapy()

        common.log_message("55% field - Performing Modifiers Check Process")
        cr.modifiers_check()

        common.log_message("75% field - Performing Billing Scrub Process")
        cr.billing_scrub()
    except Exception as error:
        common.log_message(str(error), "ERROR")
        cr.browser.capture_page_screenshot(
            os.path.join(
                os.environ.get("ROBOT_ROOT", os.getcwd()),
                "output",
                "Something_went_wrong.png",
            )
        )
        try:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            del exc_info
        except Exception as ex:
            print(str(ex))
            pass
        exit(1)

    common.log_message("100% field - Processes Complete")
    common.log_message("End Trumpet Behavioral Health - Rosey")
    common.google_logger.send_all_logs()


if __name__ == "__main__":
    main()
