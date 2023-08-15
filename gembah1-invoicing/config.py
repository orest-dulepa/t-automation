import os

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

CREDENTIALS_NAME: dict = {
    'quickbooks': 'Quickbooks',
    'slack': 'Gembah Slack',
}
TEMP_FOLDER: str = os.path.join(os.getcwd(), 'temp')

OUTPUT_FOLDER: str = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output')

SPREADSHEET_NAME: str = 'AM Bot Template- Clean'


class Account:
    def __init__(self, cred_path: str, scopes: list):
        self.cred_path = os.path.abspath(cred_path)
        self.token_path = os.path.join(os.path.dirname(self.cred_path), 'token.json')
        self.scopes = scopes


BOT_ACCOUNT = Account('settings/credentials.json',
                      scopes=['https://mail.google.com/',
                              'https://www.googleapis.com/auth/drive',
                              'https://www.googleapis.com/auth/spreadsheets'])
