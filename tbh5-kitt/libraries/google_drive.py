import os
import io
import requests
import json

from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient import discovery
from libraries import common


class GoogleDrive:
    def __init__(self):
        self.credentials = service_account.Credentials.from_service_account_file(
            os.path.join('settings', 'service_account_key.json')
        )
        self.service = None
        self.path_to_file = ''

    def download_file_by_name(self, file_name='TBH Payor Info.xlsx'):
        # Call the Drive v3 API
        try:
            self.service = discovery.build('drive', 'v3', credentials=self.credentials, cache_discovery=False)
        except Exception as error:
            common.log_message(str(error), 'ERROR')
            service_json = json.loads(requests.get('https://www.googleapis.com/discovery/v1/apis/drive/v3/rest').content)
            self.service = discovery.build_from_document(service_json, credentials=self.credentials)

        items: list = []
        results = self.service.files().list(fields="nextPageToken, files(id, name)").execute()
        items += results.get('files', [])
        while results.get('nextPageToken', ''):
            results = self.service.files().list(fields="nextPageToken, files(id, name)", pageToken=results['nextPageToken']).execute()
            items += results.get('files', [])

        file_id = ''
        for item in items:
            if os.path.splitext(item['name'].lower())[0].strip() == os.path.splitext(file_name.lower())[0].strip():
                file_id = item['id']
        if file_id == '':
            raise Exception('{} file not found.'.format(file_name))

        self.path_to_file = os.path.join('output', file_name)

        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(self.path_to_file, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        print('{} file downloaded'.format(file_name))

    def download_file_by_part_of_name(self, check_number: str) -> str:
        # Call the Drive v3 API
        try:
            self.service = discovery.build('drive', 'v3', credentials=self.credentials, cache_discovery=False)
        except Exception as error:
            common.log_message(str(error), 'ERROR')
            service_json = json.loads(requests.get('https://www.googleapis.com/discovery/v1/apis/drive/v3/rest').content)
            self.service = discovery.build_from_document(service_json, credentials=self.credentials)

        results = self.service.files().list(pageSize=250, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        file_id: str = ''
        file_name: str = ''
        for item in items:
            if check_number.lower() in item['name'].lower():
                file_id = item['id']
                file_name = item['name']

        if not file_id:
            return ''

        if not os.path.exists(os.path.join('temp', 'pdf')):
            os.mkdir(os.path.join('temp', 'pdf'))
        self.path_to_file = os.path.join('temp', 'pdf', file_name)

        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(self.path_to_file, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        print('{} file downloaded'.format(file_name))
        return self.path_to_file

    def upload_file(self, path_to_file: str):
        # Call the Drive v3 API
        try:
            self.service = discovery.build('drive', 'v3', credentials=self.credentials, cache_discovery=False)
        except Exception as error:
            common.log_message(str(error), 'ERROR')
            service_json = json.loads(requests.get('https://www.googleapis.com/discovery/v1/apis/drive/v3/rest').content)
            self.service = discovery.build_from_document(service_json, credentials=self.credentials)

        items: list = []
        results = self.service.files().list(fields="nextPageToken, files(id, name)").execute()
        items += results.get('files', [])
        while results.get('nextPageToken', ''):
            results = self.service.files().list(fields="nextPageToken, files(id, name)", pageToken=results['nextPageToken']).execute()
            items += results.get('files', [])

        file_id = ''
        for item in items:
            if os.path.splitext(item['name'].lower())[0].strip() == os.path.splitext(os.path.basename(path_to_file).lower())[0].strip():
                file_id = item['id']
                break
        if file_id == '':
            raise Exception('{} file not found.'.format(path_to_file))

        file = self.service.files().get(fileId=file_id).execute()
        media_body = MediaFileUpload(path_to_file, mimetype=file['mimeType'], resumable=True)
        updated_file = self.service.files().update(fileId=file_id, media_body=media_body).execute()
