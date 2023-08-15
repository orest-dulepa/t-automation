import os
import datetime

from RPA.Robocloud.Items import Items
from RPA.Robocloud.Secrets import Secrets
from ta_bitwarden_cli import ta_bitwarden_cli as ta

from libraries import common, central_reach, send_message, file_uploader


CREDENTIALS_NAME = {
    "central reach": "Butterfly Effects Central Reach",
    "office365Apps": "Butterfly Effects Microsoft Online Apps",
}
CREDENTIALS = {"example": {"login": "", "password": "", "url": "", "otp": ""}}


def get_bitwarden_credentials(credentials_name):
    secrets = Secrets()
    bitwarden_credentials = secrets.get_secret(credentials_name)
    return bitwarden_credentials


def change_date_format(date):
    date = date.split("/")
    date = datetime.datetime(int(date[2]), int(date[0]), int(date[1]))
    new_date = date.strftime("%Y-%m-%d")
    return new_date


def get_inputs():
    library = Items()
    library.load_work_item_from_environment()
    client_id = str(library.get_work_item_variable("in_ClientID")).strip()
    start_date = change_date_format(library.get_work_item_variable("in_StartDate"))
    end_date = change_date_format(library.get_work_item_variable("in_EndDate"))

    common.log_message(
        "Received input data: {}, {}, {}".format(client_id, start_date, end_date)
    )
    if not client_id:
        common.log_message("Client ID is empty. Process terminated")
        exit(0)
    return client_id, start_date, end_date


def main():
    common.log_message("Start Butterfly Effects - Initial Invoicing")
    common.print_version()

    if not os.path.exists(
        os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "temp")
    ):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "temp"))
    if not os.path.exists(
        os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "temp", "pdf")
    ):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "temp", "pdf"))
    if not os.path.exists(
        os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "output")
    ):
        os.mkdir(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "output"))

    # get credentials
    bitwarden_credentials = get_bitwarden_credentials("bitwarden_credentials")
    global CREDENTIALS
    global CREDENTIALS_NAME
    bw = ta.Bitwarden(bitwarden_credentials)
    CREDENTIALS = bw.get_credentials(CREDENTIALS_NAME)
    client_id, start_date, end_date = get_inputs()

    common.log_message("10% field - Logging into system", "INFO")
    cr = central_reach.CentralReach(CREDENTIALS["central reach"])
    if not cr.is_site_available:
        common.log_message("CentralReach site is not available", "ERROR")
        exit(1)

    common.log_message("20% field - Bot is filtering the data in Central Reach", "INFO")
    client_email: str = ''
    try:
        client_email = cr.filtering_data(client_id, start_date, end_date)
    except Exception as ex:
        common.log_message("Unable to get client email", "INFO")
        print(str(ex))
        exit(0)
    common.log_message("Client email is {}".format(client_email))

    common.log_message("40% field - Bot is generating the PDF invoice", "INFO")
    invoice_number, invoice_path = cr.bulk_generate_invoices()
    common.log_message("Downloaded invoice number is {}".format(invoice_number))
    status = file_uploader.upload_file(
        invoice_number, invoice_path, CREDENTIALS["office365Apps"]
    )

    common.log_message(
        "70% field - Bot is updating client notes in Central Reach", "INFO"
    )
    cr.update_contact_note(client_id, invoice_number)

    common.log_message("90% field - Bot is sending the invoice via email", "INFO")
    send_message.send(
        invoice_number, invoice_path, client_email, CREDENTIALS["office365Apps"]
    )

    common.log_message("100% field - Bot has completed its task", "INFO")
    common.log_message("End Butterfly Effects - Initial Invoicing")


if __name__ == "__main__":
    main()
