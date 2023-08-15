import os

SENT_MAIL_TO_CLIENT = True

REPORT_RECIPIENT = ''

CREDENTIALS_NAME = {
    'central reach': 'Behavioral Healthworks Central Reach',
}
TEMP_FOLDER = os.path.join(os.getcwd(), 'temp')

OUTPUT_FOLDER = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output')


class Account:
    def __init__(self, cred_path: str, scopes: list):
        self.cred_path = os.path.abspath(cred_path)
        self.token_path = os.path.join(os.path.dirname(self.cred_path), 'token.json')
        self.scopes = scopes


BOT_ACCOUNT = Account('credentials/ta/credentials.json',
                      scopes=['https://www.googleapis.com/auth/gmail.send',
                              'https://www.googleapis.com/auth/drive.file'])

ACCOUNTING_ACCOUNT = Account('credentials/accounting/credentials.json',
                             scopes=['https://www.googleapis.com/auth/gmail.send'])
