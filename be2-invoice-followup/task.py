from RPA.Robocloud.Items import Items
from RPA.Robocloud.Secrets import Secrets
import os
from libraries import common, office365
from ta_bitwarden_cli.ta_bitwarden_cli import Bitwarden
from libraries.central_reach import CentralReach
from libraries.domo import DomoAPI


CREDENTIALS_NAME = {
    'domo': 'Butterfly Effects DOMO Login',
    'central reach': 'Butterfly Effects Central Reach',
    'office365': 'Butterfly Effects Microsoft Online Apps'
}
CREDENTIALS = {
    'example': {'login': '', 'password': '', 'url': '', 'otp': ''}
}


def get_bitwarden_credentials(credentials_name):
    secrets = Secrets()
    bitwarden_credentials = secrets.get_secret(credentials_name)
    return bitwarden_credentials


def get_client_id():
    library = Items()
    library.load_work_item_from_environment()
    client_id = library.get_work_item_variable('client_id')
    common.log_message('Received client id: {}'.format(client_id))
    return client_id


def main():
    common.log_message('Start Butterfly Effects - Invoice Followup')
    common.print_version()

    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp'))
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'pdf')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'pdf'))
    if not os.path.exists(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'output')):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'temp', 'output'))

    bitwarden_credentials: dict = get_bitwarden_credentials('bitwarden_credentials')
    client_id = get_client_id()

    global CREDENTIALS
    global CREDENTIALS_NAME

    br = Bitwarden(bitwarden_credentials)
    CREDENTIALS = br.get_credentials(CREDENTIALS_NAME)
    if 'domo' not in CREDENTIALS or 'central reach' not in CREDENTIALS or 'office365' not in CREDENTIALS:
        CREDENTIALS = br.get_credentials(CREDENTIALS_NAME)

    common.log_message('10% field - Preparing Queue', 'INFO')
    domo: DomoAPI = DomoAPI(CREDENTIALS['domo'])
    invoices_domo: dict = domo.get_invoices_info(client_id)

    common.log_message('30% field - Gathering Data', 'INFO')
    cr: CentralReach = CentralReach(CREDENTIALS['central reach'])
    if not cr.is_site_available:
        common.log_message('CentralReach site is not available', 'ERROR')
        exit(1)
    cr.client_id = client_id
    cr.get_client_email()
    cr.domo_invoices = list(invoices_domo.keys())
    cr.download_invoices()

    common.log_message('50% field - Preparing Email', 'INFO')
    outlook_object = office365.Office365(CREDENTIALS['office365'], client_id, cr.client_email, cr.invoices_path, invoices_domo)
    outlook_object.prepare_email()

    common.log_message('65% field - Bulk Applying Payments', 'INFO')
    cr.update_billing_manager()

    common.log_message('80% field - Updating Notes', 'INFO')
    cr.update_contact_note()

    common.log_message('90% field - Sending Email', 'INFO')
    outlook_object.send_email()

    common.log_message('100% field - Record Complete', 'INFO')
    common.log_message('End Butterfly Effects - Invoice Followup')


if __name__ == '__main__':
    main()
