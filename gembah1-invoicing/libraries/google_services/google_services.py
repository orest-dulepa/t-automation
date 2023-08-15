from os import path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from config import Account


class GoogleServices:
    @staticmethod
    def _get_credentials(account: Account):
        credentials = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if path.exists(account.token_path):
            credentials = Credentials.from_authorized_user_file(account.token_path, account.scopes)
        # If there are no (valid) credentials available, let the user log in.
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(account.cred_path, account.scopes)
                credentials = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(account.token_path, 'w') as token:
                token.write(credentials.to_json())

        return credentials
