import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders


class MailMessage:
    """This class describes MailMessage object, and has method to send
        MailMessage object with optional attachment"""

    def __init__(self, bot_identity, bot_credentials):
        self.msg = MIMEMultipart()
        self.msg['From'] = bot_identity
        self.bot_creds = bot_credentials
        print('')

    def send_message(self, subject: str, body: str, recepient: str, cc: str = '', attachment: str = '',
                     remove_attachment=False):
        try:
            self.msg['To'] = recepient
            self.msg['CC'] = cc
            self.msg['Subject'] = subject
            self.msg.attach(MIMEText(body, 'plain'))
            if not attachment == '':
                self.add_attachment(attachment)
            server = smtplib.SMTP('smtp.office365.com', 587)
            server.starttls(context=ssl.create_default_context())
            server.login(self.bot_creds['login'], self.bot_creds['password'])
            server.send_message(self.msg)
            server.quit()

            if remove_attachment:
                os.remove(attachment)
            return 'Message sent'

        except Exception as ex:
            return ex

    def add_attachment(self, attachment_path):
        path, filename = os.path.split(attachment_path)
        attachment_obj = open(attachment_path, 'rb')
        part = MIMEBase('application', "octet-stream")
        part.set_payload(attachment_obj.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        self.msg.attach(part)
