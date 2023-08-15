import os
import re
import time
from glob import glob
from RPA.Browser.Selenium import Selenium
from RPA.Outlook.Application import Application


class Outlook:
    def __init__(self, path_to_current_folder, is_test_run: bool = False):
        app = Application()
        app.open_application()
        namespace = app.app.GetNamespace("MAPI")
        self.test_run = is_test_run
        self.inbox = namespace.Folders["Public Folders - TA@rsmalaw.com"].Folders['All Public Folders'].Folders['Bankruptcy'].Items
        # self.inbox = namespace.GetDefaultFolder(6).Items
        self.inbox.Sort("[ReceivedTime]", True)
        self.raw_mail = None
        self.found_mail = None
        self.browser: Selenium = Selenium()
        root_path = os.environ.get("ROBOT_ROOT", os.getcwd())
        self.path_to_temp = os.path.join(root_path, 'temp')
        self.path_to_folder = path_to_current_folder

    def _message_to_dictionary(self, message):
        msg = dict()
        msg["Subject"] = getattr(message, "Subject", "<UNKNOWN>")
        # rt = getattr(message, "ReceivedTime", "<UNKNOWN>")
        # msg["ReceivedTime"] = rt.isoformat()
        # msg["ReceivedTimeTimestamp"] = datetime(
        #     rt.year, rt.month, rt.day, rt.hour, rt.minute, rt.second
        # ).timestamp()
        so = getattr(message, "SentOn", "<UNKNOWN>")
        msg["SentOn"] = so.isoformat()
        msg["EntryID"] = getattr(message, "EntryID", "<UNKNOWN>")
        se = getattr(message, "Sender", "<UNKNOWN>")
        if message.SenderEmailType == "EX":
            sender = se.GetExchangeUser().PrimarySmtpAddress
        else:
            sender = message.SenderEmailAddress
        msg["Sender"] = sender
        msg["Size"] = getattr(message, "Size", "<UNKNOWN>")
        msg["Body"] = getattr(message, "Body", "<UNKNOWN>")
        return msg

    def find_mail(self, subject: str, sender: str):
        print('starting processing letters')
        if self.test_run:
            print('pretending to search mail')
        else:
            for msg in self.inbox:
                m = self._message_to_dictionary(msg)
                if subject in m['Subject'] and sender in m['Sender']:
                    self.found_mail = m
                    self.raw_mail = msg
                    print(m)
                    break

    def get_linked_file_by_re(self, pattern):
        if self.test_run:
            print('pretending to get file')
            return r'C:\fakepath\fakefile.pdf'
        else:
            preferences = {
                'download.default_directory': self.path_to_temp,
                'plugins.always_open_pdf_externally': True,
                'download.directory_upgrade': True,
                'download.prompt_for_download': False
            }
            file_link = re.findall(pattern, self.found_mail['Body'])[0]
            self.browser.open_available_browser(file_link, preferences=preferences)
            try:
                self.browser.click_element_when_visible('//button')
            except:  # not working
                print('No open button')
            time.sleep(10)
            list_of_files = glob(os.path.join(self.path_to_temp, '*.pdf'))
            latest_file = max(list_of_files, key=os.path.getctime)
            new_filepath = os.path.join(self.path_to_folder, 'Filed NOPC.pdf')
            os.rename(latest_file, new_filepath)
            return new_filepath

    def delete_mail(self):
        if self.test_run:
            print('mail deleted placeholder')
        else:
            self.raw_mail.Delete()
