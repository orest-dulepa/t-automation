import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders


def send(invoice_id, file_path, to_email, credentials):
    try:
        filename = invoice_id + '.pdf'
        msg_text = open(os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'templates', 'msg.txt')).read()

        msg = MIMEMultipart()
        msg['From'] = 'alex.lucas@butterflyeffects.com'
        msg['To'] = to_email
        msg['CC'] = 'billing@butterflyeffects.com'
        msg['Subject'] = 'Butterfly Effects - Invoice ' + invoice_id
        body = msg_text
        msg.attach(MIMEText(body, 'plain'))

        attachment = open(file_path, 'rb')
        part = MIMEBase('application', "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        msg.attach(part)

        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls(context=ssl.create_default_context())
        server.login(credentials['login'], credentials['password'])
        server.send_message(msg)
        server.quit()

        os.remove(file_path)
        return 'The message has been sent'

    except Exception as ex:
        print(str(ex))
