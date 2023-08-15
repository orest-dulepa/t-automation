import os
from RPA.Robocloud.Items import Items
from RPA.Robocloud.Secrets import Secrets
from libraries import bitwarden, common
from libraries.central_reach import CentralReach
import traceback
import sys


credentials_name = {
    'central reach': 'Butterfly Effects Central Reach',
}


def get_bitwarden_credentials(bitwarden_credential_name: str = 'bitwarden_credentials') -> dict:
    secrets = Secrets()
    bitwarden_credentials = secrets.get_secret(bitwarden_credential_name)

    return bitwarden_credentials


def get_client_id() -> str:
    library = Items()
    library.load_work_item_from_environment()
    client_id = library.get_work_item_variable('client_id')
    common.log_message('Received client id: {}'.format(client_id))

    return client_id


def main():
    common.log_message('Start Butterfly Effects - Primary Claims')
    common.print_version()

    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp'))
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'pdf')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'pdf'))

    client_id = get_client_id()

    bitwarden_credentials = get_bitwarden_credentials('bitwarden_credentials')
    credentials = bitwarden.get_credentials(bitwarden_credentials, credentials_name)

    cr = CentralReach(credentials['central reach'])
    if not cr.is_site_available:
        common.log_message('CentralReach site is not available', 'ERROR')
        exit(1)
    cr.client_id = client_id
    common.log_message('Log In Completed')
    try:
        common.log_message('Performing Global Audit Check')
        cr.find_duplicates()
        cr.overlap_check_by_provider()
        common.log_message('Global Audit Check Complete')

        common.log_message('Filtering Claims')
        cr.apply_filter_to_claims()
        common.log_message('Filtering Claims Completed')

        cr.open_new_tab()
        cr.cr_main_process()
        common.log_message('Process Complete')
    except Exception as ex:
        common.log_message(str(ex), 'ERROR')
        cr.browser.capture_page_screenshot(
            os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output', 'Something_went_wrong.png')
        )
        try:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            del exc_info
        except Exception as ex:
            print(str(ex))
        exit(1)
    finally:
        common.log_message('End Butterfly Effects - Primary Claims')


if __name__ == '__main__':
    main()
