from googleapiclient.discovery import build
from config import Account
from libraries.google_services.google_services import GoogleServices


class GoogleDrive(GoogleServices):
    def __init__(self, account: Account):
        self.service = build('drive', 'v3', credentials=self._get_credentials(account), cache_discovery=False)

    def get_spreadsheet_id_by_name(self, spreadsheet_name: str) -> str:
        files = self.service.files().list(
            fields='nextPageToken, files(id, name, mimeType)'
        ).execute()

        for file in files['files']:
            if file['name'].lower() == spreadsheet_name.lower():
                return file['id']
        return ''
