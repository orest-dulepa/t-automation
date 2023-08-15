import mimetypes
from datetime import datetime
from os import path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import Account
from libraries.google_services.google_services import GoogleServices


class GoogleDrive(GoogleServices):
    def __init__(self, account: Account):
        self.service = build('drive', 'v3', credentials=self._get_credentials(account), cache_discovery=False)

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
