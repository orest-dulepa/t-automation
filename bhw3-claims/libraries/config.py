import os

from RPA.Robocloud.Items import Items
from RPA.Robocloud.Secrets import Secrets
from ta_bitwarden_cli import ta_bitwarden_cli as ta
from libraries import common as com
from libraries.excel import ExcelInterface


class Account:
    def __init__(self, cred_path: str, scopes: list):
        self.cred_path = os.path.abspath(cred_path)
        self.token_path = os.path.join(os.path.dirname(self.cred_path), 'token.json')
        self.scopes = scopes

BOT_ACCOUNT = Account('credentials/ta/credentials.json',
                      scopes=['https://www.googleapis.com/auth/gmail.send',
                              'https://www.googleapis.com/auth/drive.file'])


CREDENTIALS_NAME = {
    'central reach': 'Behavioral Healthworks Central Reach',
}

def get_credentials():
    bw = ta.Bitwarden(get_bitwarden_credentials())
    return bw.get_credentials(CREDENTIALS_NAME)

def get_bitwarden_credentials() -> dict:
    bitwarden_credentials = None
    try:
        secrets = Secrets()
        bitwarden_credentials = secrets.get_secret('bitwarden_credentials')

    except Exception as ex:
        com.log_message('Unable to get "bitwarden_credentials". Reason: ' + str(ex), 'ERROR')
        exit(1)


    return bitwarden_credentials


def get_input() -> (str, str):
    try:
        library = Items()
        library.load_work_item_from_environment()
        start_date: str = library.get_work_item_variable('start_date')
        end_date: str = library.get_work_item_variable('end_date')

        com.log_message(f'Received input data:  {start_date}, {end_date}')
    except:
        com.log_message(f'Unable to received input data. Therefore being set default values', "WARN")
        start_date: str = "01/01/2021"
        end_date: str = "01/31/2021"
        print("Start date - " + start_date)
        print("End date - "+ end_date)

    return start_date, end_date


ACCEPTABLE_LOCATIONS ={
    "Home",
    "School",
    "Office",
    "Telehealth"
}



