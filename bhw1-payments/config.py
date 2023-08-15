import os
from RPA.Robocloud.Secrets import Secrets
from RPA.Robocloud.Items import Items

from ta_bitwarden_cli import ta_bitwarden_cli as ta
from datetime import datetime, timedelta
from libraries import common as com


def get_bitwarden_data(credentials_name="bitwarden_credentials"):
    creds = {
        "cr": "Behavioral Healthworks Central Reach",
    }
    secrets = Secrets()
    if BITWARDEN_ENV == "local":
        bitwarden_credentials = {
            "username": os.getenv("BITWARDEN_USERNAME"),
            "password": os.getenv("BITWARDEN_PASSWORD"),
        }
    else:
        bitwarden_credentials = secrets.get_secret(credentials_name)
    bw = ta.Bitwarden(bitwarden_credentials)
    return bw.get_credentials(creds)


def get_ta_input():
    if EXECUTION_ENV == "local":
        check_number = os.getenv("CHECK_NUMBER")
        check_date = os.getenv("CHECK_DATE")
        email_recipient = os.getenv("EMAIL_RECIPIENT")
        invoice_file = os.getenv("INVOICE_FILE")
    else:
        library = Items()
        library.load_work_item_from_environment()
        check_number = library.get_work_item_variable("check_number")
        check_date = library.get_work_item_variable("check_date")
        email_recipient = library.get_work_item_variable("email_recipient")
        invoice_file = library.get_work_item_variable("invoice_file")
    return check_number, check_date, email_recipient, invoice_file


# local or robocloud
BITWARDEN_ENV = os.getenv("BITWARDEN_ENV", "local")

# local or ta
EXECUTION_ENV = os.getenv("EXECUTION_ENV", "local")

# cancel or apply
BOT_MODE = os.getenv("BOT_MODE", "cancel")

BITWARDEN_DATA = get_bitwarden_data()

CHECK_NUMBER, CHECK_DATE, EMAIL_RECIPIENT, INVOICE_FILE = get_ta_input()
