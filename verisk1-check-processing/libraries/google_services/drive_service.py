from locale import format
from googleapiclient.discovery import build, build_from_document
from config import Account
from libraries.google_services.google_services import GoogleServices
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import os
import io
import requests
import json


class GoogleDrive(GoogleServices):
    def __init__(self, account: Account):
        self.credentials = self._get_credentials(account)
        self.service = build('drive', 'v3', credentials=self.credentials, cache_discovery=False)

    def get_item_id(self, name: str) -> str:
        items: list = []
        results = self.service.files().list(fields="nextPageToken, files(id, name)").execute()
        items += results.get('files', [])
        while results.get('nextPageToken', ''):
            results = self.service.files().list(fields="nextPageToken, files(id, name, mimeType)",
                                                pageToken=results['nextPageToken']).execute()
            items += results.get('files', [])

        file_id: str = ''
        for item in items:
            if os.path.splitext(item['name'].lower())[0].strip() == os.path.splitext(name.lower())[0].strip():
                file_id = item['id']
                break
        if not file_id:
            raise Exception('{} file not found.'.format(name))
        return file_id

    def download_file_by_name(self, file_name: str, path_to_temp: str, file_id: str = '') -> str:
        if not file_id:
            file_id = self.get_item_id(file_name)

        if not os.path.exists(path_to_temp):
            os.mkdir(path_to_temp)

        path_to_file = os.path.join(path_to_temp, file_name)

        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(path_to_file, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        print('{} file downloaded'.format(file_name))
        return path_to_file

    def upload_file(self, path_to_file: str, parent_folder_id: str = '', file_name: str = ''):
        # Call the Drive v3 API
        try:
            self.service = build('drive', 'v3', credentials=self.credentials, cache_discovery=False)
        except Exception as error:
            print(str(error), 'ERROR')
            service_json = json.loads(
                requests.get('https://www.googleapis.com/discovery/v1/apis/drive/v3/rest').content)
            self.service = build_from_document(service_json, credentials=self.credentials)

        if not file_name:
            file_name = os.path.basename(path_to_file)
        file_metadata = {
            'name': file_name,
            'parents': [parent_folder_id],
            'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        media = MediaFileUpload(
            path_to_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            resumable=True
        )
        updated_file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    def update_file(self, path_to_file: str, _file_id: str = '', file_name: str = ''):
        if not file_name:
            file_name = os.path.basename(path_to_file)
        # Call the Drive v3 API
        try:
            self.service = build('drive', 'v3', credentials=self.credentials, cache_discovery=False)
        except Exception as error:
            print(str(error), 'ERROR')
            service_json = json.loads(
                requests.get('https://www.googleapis.com/discovery/v1/apis/drive/v3/rest').content)
            self.service = build_from_document(service_json, credentials=self.credentials)

        file_id = _file_id
        if not _file_id:
            items: list = []
            results = self.service.files().list(fields="nextPageToken, files(id, name)").execute()
            items += results.get('files', [])
            while results.get('nextPageToken', ''):
                results = self.service.files().list(fields="nextPageToken, files(id, name)",
                                                    pageToken=results['nextPageToken']).execute()
                items += results.get('files', [])

            file_id = ''
            for item in items:
                if os.path.splitext(item['name'].lower())[0].strip() == \
                        os.path.splitext(file_name.lower())[0].strip():
                    file_id = item['id']
                    break
            if file_id == '':
                raise Exception('{} file not found.'.format(path_to_file))

        file = self.service.files().get(fileId=file_id).execute()
        media_body = MediaFileUpload(path_to_file, mimetype=file['mimeType'], resumable=True)
        updated_file = self.service.files().update(fileId=file_id, media_body=media_body).execute()

    def get_items_in_folder(self, folder_name: str, _folder_id: str = '') -> list:
        if _folder_id:
            folder_id = _folder_id
        else:
            folder_id: str = self.get_item_id(folder_name)

        items: list = []
        results = self.service.files().list(q=f"'{folder_id}' in parents", fields="nextPageToken, files(id, name, mimeType)").execute()
        items += results.get('files', [])
        while results.get('nextPageToken', ''):
            results = self.service.files().list(q=f"'{folder_id}' in parents", fields="nextPageToken, files(id, name)", pageToken=results['nextPageToken']).execute()
            items += results.get('files', [])

        # check mimeType
        # 'mimeType': 'application/vnd.google-apps.folder'
        # 'mimeType': 'application/pdf'
        # 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return items

    def download_pdf_from_folder(self, folder_name: str, path_to_temp: str):
        files: list = self.get_items_in_folder(folder_name)

        for file in files:
            if 'pdf' in file['mimeType']:
                self.download_file_by_name(file['name'], path_to_temp, file['id'])

    def get_or_create_folder(self, folder_name: str, items: list, parent_folder_id: str, is_create: bool = False):
        folder_id: str = ''
        if not items:
            items: list = self.get_items_in_folder('parent_folder_name', parent_folder_id)

        for file in items:
            if not file.get('mimeType'):
                continue
            if 'folder' not in file.get('mimeType'):
                continue
            if file['name'] == folder_name:
                folder_id = file['id']
                break

        if not folder_id and is_create:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            new_folder = self.service.files().create(body=file_metadata, fields='id').execute()
            folder_id = new_folder['id']
        return folder_id

    @staticmethod
    def get_file_id(file_name: str, items: list):
        file_id: str = ''

        for file in items:
            if file['name'] == file_name:
                file_id = file['id']
                break
        return file_id
