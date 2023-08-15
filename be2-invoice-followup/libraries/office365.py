from libraries import common
import os
import datetime
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from ntpath import basename
import email
import imaplib
import functools


def compare(item1, item2):
    try:
        tmp_date1 = datetime.datetime.strptime(item1['Date'], '%a, %d %b %Y %H:%M:%S %z')
        tmp_date2 = datetime.datetime.strptime(item2['Date'], '%a, %d %b %Y %H:%M:%S %z')
        if tmp_date1.timestamp() > tmp_date2.timestamp():
            return -1
        elif tmp_date1.timestamp() < tmp_date2.timestamp():
            return 1
    except:
        pass
    return 0


class Office365:
    list_of_emails = []
    is_reply = False
    mail_item = None

    def __init__(self, credentials: dict, client_id: str, client_email: str, invoices_cr: dict, invoices_domo: dict):
        self.client_id: str = client_id
        self.email_subject: str = 'Butterfly Effects - Invoice {}'.format(str.join(', ', invoices_domo.keys()))
        self.email_body: str = ''
        self.email_to: str = client_email
        self.email_from: str = 'Patient.Invoicing@ButterflyEffects.com'
        self.email_cc: str = 'billing@butterflyeffects.com'
        self.invoices_cr: dict = invoices_cr
        self.invoices_domo: dict = invoices_domo
        self.credentials: dict = credentials

    def generate_email_body(self, is_reply_email: bool):
        if is_reply_email:
            path_to_template = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()),  'templates', 'reply_email_template.txt')
        else:
            path_to_template = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()),  'templates', 'new_email_template.txt')

        with open(path_to_template, 'r') as file:
            template = file.read()

        invoice_rows: list = []
        for invoice_domo_number, domo_data in self.invoices_domo.items():
            if invoice_domo_number in self.invoices_cr:
                tmp_domo_amount = float(domo_data['amount'].replace('$', '').replace(',', ''))
                tmp_cr_amount = float(self.invoices_cr[invoice_domo_number]['amount'].replace('$', '').replace(',', ''))
                if round(tmp_domo_amount, 2) == round(tmp_cr_amount, 2):
                    invoice_rows.append("•       Invoice {} - {}\n".format(invoice_domo_number, self.invoices_cr[invoice_domo_number]['amount']))
                else:
                    invoice_rows.append("•       Invoice {} - {} -- ${} outstanding\n".format(invoice_domo_number, self.invoices_cr[invoice_domo_number]['amount'], domo_data['amount']))
            else:
                common.log_message("Can't compare DOMO invoice #{} with Central Reach because it does not exist.".format(invoice_domo_number))
        if len(invoice_rows) == 0:
            common.log_message("Something went wrong. Can't compare DOMO and Central Reach invoices", 'ERROR')
            exit(1)
        self.email_body = template.replace('{invoices}', str.join('', invoice_rows))

    def search_email(self, connection, folder):
        status, folder_id = connection.select(folder)
        status, email_numbers = connection.search(None, '(TEXT "' + self.client_id + '")')
        list_of_numbers = email_numbers[0].split()
        for number in list_of_numbers:
            try:
                is_email_found = False
                status, data = connection.fetch(number, "(RFC822)")
                raw_email_string = data[0][1].decode('utf-8')
                email_message = email.message_from_string(raw_email_string)
                for part in email_message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                    file_name = part.get_filename()
                    if file_name is None:
                        continue
                    for invoice in self.invoices_domo.keys():
                        if invoice in file_name and file_name.lower().endswith('.pdf'):
                            self.list_of_emails.append(email_message)
                            is_email_found = True
                            break
                    if is_email_found:
                        break
            except Exception as e:
                common.log_message(str(e), 'ERROR')
                continue

    def prepare_email(self):
        original = None
        connection = imaplib.IMAP4_SSL("outlook.office365.com")
        connection.login(self.credentials['login'], self.credentials['password'])
        self.search_email(connection, 'Inbox')
        self.search_email(connection, '"Sent Items"')
        self.is_reply = len(self.list_of_emails) > 0

        self.mail_item = MIMEMultipart("mixed")
        if self.is_reply:
            common.log_message('A valid email thread was found')
            res = sorted(self.list_of_emails, key=functools.cmp_to_key(compare))
            original = res[0]
            self.email_subject = original["Subject"]
        else:
            common.log_message('An email thread was not found. Creating a new email.')
        self.generate_email_body(self.is_reply)

        body = MIMEMultipart("alternative")
        body.attach(MIMEText(self.email_body, "plain"))
        # body.attach(MIMEText(self.email_body, "html"))
        self.mail_item.attach(body)

        self.mail_item["To"] = self.email_to
        self.mail_item["From"] = self.email_from
        self.mail_item['CC'] = self.email_cc
        self.mail_item["Subject"] = self.email_subject

        if self.is_reply:
            self.mail_item["In-Reply-To"] = original["Message-ID"]
            self.mail_item["References"] = original["Message-ID"]
        for invoice_cr, value_cr in self.invoices_cr.items():
            attachment = open(value_cr['path'], "rb")
            p = MIMEBase('application', 'octet-stream')
            p.set_payload(attachment.read())
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', "attachment; filename= %s" % basename(value_cr['path']))
            self.mail_item.attach(p)

    def send_email(self):
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls(context=ssl.create_default_context())
        server.login(self.credentials['login'], self.credentials['password'])
        server.send_message(self.mail_item)
        common.log_message('The email was sent successfully')
        server.quit()
