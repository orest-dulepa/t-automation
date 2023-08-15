import os
import platform
from shutil import copyfile

PROD: bool = False
try:
    file = open('ENV')
    try:
        if file.read().strip().upper() == 'PROD':
            PROD = True
    except Exception as ex:
        print('Error reading ENV file. {}'.format(str(ex)))
    finally:
        file.close()
except Exception as e:
    print('ENV file not found. {}'.format(str(e)))

TEMP_FOLDER: str = os.path.join(os.getcwd(), 'tmp')
platform_type: str = platform.system().lower()
if platform_type == 'linux':
    TEMP_FOLDER = '/tmp'


class Account:
    def __init__(self, cred_path: str, scopes: list):
        self.cred_path = os.path.abspath(cred_path)
        self.token_path = os.path.join(os.path.dirname(self.cred_path), 'token.json')
        self.scopes = scopes


credentials_path = 'settings/credentials.json'
if platform_type == 'linux':
    credentials_path = os.path.join(TEMP_FOLDER, 'credentials.json')
    copyfile('settings/credentials.json', credentials_path)
    copyfile('settings/token.json', os.path.join(TEMP_FOLDER, 'token.json'))

BOT_ACCOUNT = Account(credentials_path,
                      scopes=['https://mail.google.com/',
                              'https://www.googleapis.com/auth/drive',
                              'https://www.googleapis.com/auth/spreadsheets'])
