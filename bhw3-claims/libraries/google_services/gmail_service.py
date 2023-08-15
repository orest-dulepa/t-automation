import base64
import mimetypes
import os
import os.path
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from retry import retry

from config import Account
from libraries.google_services.google_services import GoogleServices


class Gmail(GoogleServices):
    def __init__(self, account: Account):
        self.service = build('gmail', 'v1', credentials=self._get_credentials(account), cache_discovery=False)

    @staticmethod
    def __make_attachment(file):
        content_type, encoding = mimetypes.guess_type(file)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        with open(file, 'rb') as fp:
            if main_type == 'text':
                msg = MIMEText(fp.read().decode(), _subtype=sub_type)
            elif main_type == 'image':
                msg = MIMEImage(fp.read(), _subtype=sub_type)
            elif main_type == 'audio':
                msg = MIMEAudio(fp.read(), _subtype=sub_type)
            elif main_type == 'application':
                msg = MIMEApplication(fp.read(), _subtype=sub_type)
            else:
                msg = MIMEBase(main_type, sub_type)
                msg.set_payload(fp.read())

        msg.add_header('Content-Id', f'<{os.path.basename(file)}>')
        msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file))
        return msg

    @classmethod
    def __make_message(cls, to, subject, html_body, cc='', attachments: list = []):
        message = MIMEMultipart(_subtype='related')
        message['to'] = to
        message['cc'] = cc
        message['subject'] = subject

        html_part = MIMEText(html_body, _subtype='html')
        message.attach(html_part)
        for file_path in attachments:
            attachment_part = cls.__make_attachment(file_path)
            message.attach(attachment_part)
        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    @retry(ConnectionAbortedError, delay=1, tries=8, backoff=2, max_delay=4)
    def send_message(self, to, subject, html_body, cc='', attachments: list = []):
        message = self.__make_message(to, subject, html_body, cc, attachments)
        self.service.users().messages().send(userId='me', body=message).execute()
