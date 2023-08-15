from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
import os
import io


class GoogleDrive:
    def __init__(self):
        self.credentials = service_account.Credentials.from_service_account_file(
            os.path.join('settings', 'service_account_key.json')
        )
        self.service = None
        self.path_to_file = ''

    def download_sheet_file(self):
        self.service= build('sheets', 'v4', credentials=self.credentials, cache_discovery=False)
        #sheet = self.service.spreadsheets().execute().get(spreadsheetId = "17f75uUXgH-beJNY8OR1ZXbYJ997c4SVSbQTcrJn6k7s").execute()
        result = self.service.spreadsheets().values().get(spreadsheetId="17f75uUXgH-beJNY8OR1ZXbYJ997c4SVSbQTcrJn6k7s",
                                    range="Commercial Providers (Excludes Tricare)").execute()
        print()


    def download_file_by_name(self, file_name='TBH Payor Info.xlsx'):
        self.service = build('drive', 'v3', credentials=self.credentials, cache_discovery=False)

        # Call the Drive v3 API
        results = self.service.files().list(pageSize=100, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        file_id = ''
        for item in items:
            if item['name'].lower() == file_name.lower():
                file_id = item['id']
        if file_id == '':
            print('{} file not found.'.format(file_name))
            exit(1)

        self.path_to_file = os.path.join('temp', file_name)

        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(self.path_to_file, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        print('{} file downloaded'.format(file_name))
