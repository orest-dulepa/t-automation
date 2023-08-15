import os
import datetime
import time
from google.oauth2 import service_account
from googleapiclient import discovery


class GoogleSheets:
    SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
    spreadsheet_id: str = ''
    current_row: int = 1
    timer: datetime = None
    batch_rows: list = []
    min_limit: int = 10

    def __init__(self):
        self.credentials = service_account.Credentials.from_service_account_file(
            os.path.join('settings', 'service_account_key.json'),
            scopes=self.SCOPES
        )
        self.service = None

    def set_headers(self):
        self.update_spreadsheet('Time (UTC)', 'Log Level', 'Text')

    def send_all_logs(self) -> None:
        if not self.batch_rows:
            return
        if not self.service:
            self.service = discovery.build('sheets', 'v4', credentials=self.credentials, cache_discovery=False)

        for i in range(10):
            try:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range='A' + str(self.current_row),
                    valueInputOption='USER_ENTERED',
                    body={
                        "values": self.batch_rows
                    }
                ).execute()
                self.current_row += len(self.batch_rows)
                self.batch_rows = []
                break
            except:
                print('send_all_logs() error')
                time.sleep(30)

    def update_spreadsheet(self, date: str, level: str, value: str) -> None:
        if not self.service:
            self.service = discovery.build('sheets', 'v4', credentials=self.credentials, cache_discovery=False)

        self.batch_rows.append([date, level, value])
        if len(self.batch_rows) < self.min_limit:
            return
        if self.timer is not None and self.timer > datetime.datetime.now():
            return

        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range='A' + str(self.current_row),
                valueInputOption='USER_ENTERED',
                body={
                    "values": self.batch_rows
                }
            ).execute()

            self.current_row += len(self.batch_rows)
            self.batch_rows = []
            self.timer = None
        except:
            print('_google_sheets API')
            self.timer = datetime.datetime.now() + datetime.timedelta(0, 15)

    def create_new_spreadsheet(self, folder_name: str, sheets_name: str) -> None:
        self.service = discovery.build('drive', 'v3', credentials=self.credentials, cache_discovery=False)
        file_metadata = {
            'name': sheets_name,
            'parents': [self.get_folder_id(folder_name)],
            'mimeType': 'application/vnd.google-apps.spreadsheet',
        }
        res = self.service.files().create(body=file_metadata).execute()
        self.spreadsheet_id = res['id']

        self.service = None
        self.set_headers()

    def get_folder_id(self, folder_name: str) -> str:
        if not self.service:
            self.service = discovery.build('drive', 'v3', credentials=self.credentials, cache_discovery=False)

        items: list = []
        results = self.service.files().list(fields="nextPageToken, files(id, name)").execute()
        items += results.get('files', [])
        while results.get('nextPageToken', ''):
            results = self.service.files().list(fields="nextPageToken, files(id, name)", pageToken=results['nextPageToken']).execute()
            items += results.get('files', [])

        folder_id = ''
        for item in items:
            if item['name'].strip().lower() == folder_name.strip().lower():
                folder_id = item['id']
                break

        return folder_id
