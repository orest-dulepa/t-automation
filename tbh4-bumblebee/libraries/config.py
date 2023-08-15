from RPA.Robocloud.Secrets import Secrets
from ta_bitwarden_cli import ta_bitwarden_cli as ta
from libraries import common as com

CREDENTIALS_NAME = {
    'central reach': 'TBH Central Reach Login',
    'waystar': 'Waystar Login'
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


def get_data_using_secrets():
    try:
        secrets = Secrets()
        config_data = secrets.get_secret('config_data')
    except Exception as ex:
        com.log_message('Unable to get "config_data" from Robocorp. Reason: ' + str(ex), 'WARN')
        com.log_message("Get default 'config_data'")

        config_data: dict = {
            "filter_start_date": "03/22/2015",
            "file_name_from_gd": "invoice template 7.2020.xlsx",
            'count_clients': "0"
        }
        for key in config_data.keys():
            com.log_message(key + " - " + config_data[key])

    return config_data
