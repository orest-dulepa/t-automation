import time
import re
from googleapiclient.discovery import build
from config import Account
from libraries.google_services.google_services import GoogleServices


class Gmail(GoogleServices):
    query: str = 'from:*@intuit.com is:unread'
    userId: str = 'me'

    def __init__(self, account: Account):
        self.service = build('gmail', 'v1', credentials=self._get_credentials(account), cache_discovery=False)

    def move_to_trash_old_mail(self) -> None:
        old_mails = self.service.users().messages().list(userId=self.userId, q=self.query).execute()

        if not old_mails['resultSizeEstimate']:
            return
        for message in old_mails['messages']:
            self.service.users().messages().trash(userId=self.userId, id=message['id']).execute()

    def get_code_from_mail(self) -> str:
        mail_id: str = ''
        verification_code = ''

        for i in range(10):
            mails = self.service.users().messages().list(userId=self.userId, q=self.query).execute()
            if not mails['resultSizeEstimate']:
                time.sleep(5)
            else:
                mail_id: str = mails['messages'][0]['id']
                break
        if mail_id:
            mail_obj = self.service.users().messages().get(userId=self.userId, id=mail_id).execute()
            verification_code: str = re.findall(r'Verification code: (\d+)', mail_obj['snippet'])[0]
        self.move_to_trash_old_mail()
        return verification_code
