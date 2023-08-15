import io
import mimetypes
import os
from datetime import datetime
from os import path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from libraries.config import Account
from libraries.google_services.google_services import GoogleServices


class GoogleDrive(GoogleServices):
    def __init__(self, account: Account):
        self.service = build('drive', 'v3', credentials=self._get_credentials(account), cache_discovery=False)
        self.service_sheets = build('sheets', 'v4', credentials=self._get_credentials(account), cache_discovery=False)
        self.acc = account

    def __get_child_folders(self, folder_id):
        children = self.service.files().list(
            q=f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        ).execute()
        return children.get('files', [])

    def __create_folder(self, root_id, name):
        file_metadata = {
            'name': name,
            'parents': [root_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        return self.service.files().create(body=file_metadata).execute()

    def get_or_create_curr_month_folder(self, folder_id):
        current_month_name = datetime.now().strftime("%B %Y")
        child_folders = self.__get_child_folders(folder_id)
        for folder in child_folders:
            if folder['name'] == current_month_name:
                return folder['id']
        folder = self.__create_folder(folder_id, current_month_name)
        return folder['id']

    def create_file_in_folder(self, file_path, folder_id, file_name=''):
        file_metadata = {
            'name': file_name if file_name else path.basename(file_path),
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path,
                                mimetype=mimetypes.guess_type(file_path)[0],
                                resumable=True)
        self.service.files().create(body=file_metadata, media_body=media).execute()

    def test_export_excel(self):
        file_id = '1iR-d7Ai1eX4oSC44GabGQ6GQIeTyQTyI'
        request = self.service.files().export_media(fileId=file_id,
                                                     mimeType='application/pdf')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()


    def download_file_by_name(self, file_name='TBH Payor Info.xlsx'):

        # Call the Drive v3 API
        #{'id': '1iR-d7Ai1eX4oSC44GabGQ6GQIeTyQTyI', 'name': 'AmSe_3527077.pdf'}
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




