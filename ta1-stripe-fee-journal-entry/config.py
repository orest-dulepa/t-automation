import os
from RPA.Robocloud.Secrets import Secrets

from ta_bitwarden_cli import ta_bitwarden_cli as ta
from datetime import datetime, timedelta


def get_bitwarden_data(credentials_name: str = "bitwarden_credentials"):
    creds = {
        "stripe": "dashboard.stripe.com",
    }
    secrets = Secrets()
    if os.getenv("BOT_ENV") == "local":
        bitwarden_credentials = {
            "username": os.getenv("BITWARDEN_USERNAME"),
            "password": os.getenv("BITWARDEN_PASSWORD"),
        }
    else:
        bitwarden_credentials = secrets.get_secret(credentials_name)
    bw = ta.Bitwarden(bitwarden_credentials)
    return bw.get_credentials(creds)


BITWARDEN_DATA = get_bitwarden_data()
