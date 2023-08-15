import base64
import mimetypes
import os
import os.path
import pickle
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from retry import retry


class Gmail:
    def __init__(self):
        self.service = build(
            "gmail", "v1", credentials=self.__get_credentials(), cache_discovery=False
        )

    @staticmethod
    def __get_credentials():
        scopes = ["https://www.googleapis.com/auth/gmail.send"]
        token_path = os.path.abspath("credentials/token.pickle")
        application_name = "Orphan Payments Bot"
        credentials_path = os.path.abspath("credentials/client_secret.json")

        credentials = None
        if os.path.exists(token_path):
            with open(token_path, "rb") as token:
                credentials = pickle.load(token)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, scopes
                )
                flow.user_agent = application_name
                credentials = flow.run_local_server()
            # Save the my_credentials for the next run
            with open(token_path, "wb") as token:
                pickle.dump(credentials, token)

        return credentials

    @staticmethod
    def __make_attachment(file):
        content_type, encoding = mimetypes.guess_type(file)

        if content_type is None or encoding is not None:
            content_type = "application/octet-stream"
        main_type, sub_type = content_type.split("/", 1)

        with open(file, "rb") as fp:
            if main_type == "text":
                msg = MIMEText(fp.read().decode(), _subtype=sub_type)
            elif main_type == "image":
                msg = MIMEImage(fp.read(), _subtype=sub_type)
            elif main_type == "audio":
                msg = MIMEAudio(fp.read(), _subtype=sub_type)
            else:
                msg = MIMEBase(main_type, sub_type)
                msg.set_payload(fp.read())

        msg.add_header("Content-Id", f"<{os.path.basename(file)}>")
        msg.add_header(
            "Content-Disposition", "attachment", filename=os.path.basename(file)
        )
        return msg

    @classmethod
    def __make_message(cls, to, subject, html_body, attachments: tuple = ()):
        message = MIMEMultipart(_subtype="related")
        message["to"] = to
        message["subject"] = subject

        html_part = MIMEText(html_body, _subtype="html")
        message.attach(html_part)
        for file_path in attachments:
            attachment_part = cls.__make_attachment(file_path)
            message.attach(attachment_part)
        return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

    @retry(ConnectionAbortedError, delay=1, tries=8, backoff=2, max_delay=4)
    def send_message(self, to, subject, html_body, attachments: tuple = ()):
        message = self.__make_message(to, subject, html_body, attachments)
        self.service.users().messages().send(userId="me", body=message).execute()
