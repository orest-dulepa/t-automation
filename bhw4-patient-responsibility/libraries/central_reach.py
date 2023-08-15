import calendar
import os
from datetime import datetime

from config import (ACCOUNTING_ACCOUNT, BOT_ACCOUNT, SENT_MAIL_TO_CLIENT, TEMP_FOLDER)
from libraries.central_reach_requests import CentralReachRequests
from libraries.client import Client
from libraries.common import log_message
from libraries.google_services.gdrive_service import GoogleDrive
from libraries.google_services.gmail_service import Gmail
from libraries.report.report_constructor import ReportConstructor, Table
from libraries.utils import ScheduledMaintenanceException


class CentralReach(CentralReachRequests):
    def __init__(self, credentials: dict, start_date: datetime, end_date: datetime):
        """ Create session and login to "Central Reach" site
        :param credentials: dict with keys "login" and "password"
        """
        super().__init__()
        self.login = 'PStatements'
        self.password: str = credentials['PStatements']
        self.default_filter_name = 'PR Statements'
        self.start_date = start_date
        self.end_date = end_date
        self.clients = []
        self.warning_messages = []

        self._login_to_central_reach(self.login, self.password)
        self._insurance_eligibility_status()

    def get_client_payor_name(self, client_id):
        # Billing > Billing > filter records
        billings = self._get_billings(client_id=client_id)
        # Payor name of first billing (billings can't be empty)
        payor_name = billings[0]['PayorName']
        return payor_name

    def create_client_invoice(self, client_id) -> int:
        # Buttons "Bulk-generate Invoices" > "Yes, generate invoice *up to 5,000" > "Patient Responsibility Invoice"
        bulk_invoice_json = self._load_bulk_invoice(client_id)

        bill_to_id = None
        if len(bulk_invoice_json['billTo']) == 1:
            bill_to_id = bulk_invoice_json['billTo'][0]['Id']
        elif len(bulk_invoice_json['billTo']) > 1:
            payor_name = self.get_client_payor_name(client_id)
            for bill_to_json in bulk_invoice_json['billTo']:
                if bill_to_json['DisplayName'] == payor_name:
                    bill_to_id = bill_to_json['Id']
                    break
        if bill_to_id is None:
            raise Exception(f"Can't find right Bill To for client - {client_id}")

        required_bill_from_name = "1301 East Orangewood Avenue, Anaheim"
        for bill_from_json in bulk_invoice_json['billFrom']:
            if bill_from_json['DisplayName'] == required_bill_from_name:
                bill_from_id = bill_from_json['Id']
                break
        else:
            raise Exception(f"Can't find '{required_bill_from_name}' in bill from")

        last_day_of_month = calendar.monthlen(datetime.now().year, datetime.now().month)
        due_date = datetime.now().replace(day=last_day_of_month)

        log_message(f"Bulk Generate Invoice")
        invoice_id = self._set_bulk_invoice(bill_from_id, bill_to_id, client_id, due_date)
        return invoice_id

    def prepare_invoice_for_download(self, invoice_id) -> int:
        self._load_invoice(invoice_id)
        notes = "This is your portion after insurance, please remit payment"
        self._set_invoice_notes(invoice_id, notes)

        self._export_invoice(invoice_id)
        resource_id = self._wait_for_invoice_is_ready(invoice_id)
        return resource_id

    def get_clients(self):
        clients_json = self._load_billing_list_distincts()

        for client_json in clients_json:
            details_json = self._load_contact_details(client_json['id'])
            self.clients.append(Client(details_json))

    @staticmethod
    def send_invoice_to_client(client: Client, invoice_path: str):
        gmail = Gmail(ACCOUNTING_ACCOUNT)
        with open(os.path.abspath('libraries/client_mail_body.html')) as f:
            html_body = f.read()
        if SENT_MAIL_TO_CLIENT:
            gmail.send_message(to=client.email,
                               cc=','.join(client.additional_emails),
                               subject='Patient Responsibility Invoice',
                               html_body=html_body,
                               attachments=[invoice_path])
            if client.additional_emails:
                log_message(f"Sent invoice to {client.email} (cc - {','.join(client.additional_emails)})")
            else:
                log_message(f"Sent invoice to {client.email}")

    def make_report(self):
        report = ReportConstructor()
        report.add_text("Dear Anita,\n\nSee below for the Patient Responsibility Report showing all of the"
                        " clients that have been worked on and the status on the completion of the key steps within "
                        "the process for each client.\n")

        if self.warning_messages:
            report.add_warning_message('Note!\n{}'.format("\n".join(self.warning_messages)))

        if self.clients:
            table = Table(['Bot WorkList', 'Invoice printed', 'Invoice Saved to Folder', 'Sent email'], True)
            date_range = f"{self.start_date.strftime('%b %d, %Y')} - {self.end_date.strftime('%b %d, %Y')}"
            table.add_title(f"Clients processed in date range '{date_range}'")

            client: Client
            for client in self.clients:
                table.add_row([client.full_name, client.status.invoice_printed,
                               client.status.invoice_saved_to_folder, client.status.email_sent])
            report.add_table(table)

        report.add_footer("\nRegards,\nPatient Responsibility Bot")

        return report

    def process(self):
        log_message(f"Navigate to Billing & Apply Date Range "
                    f"'{self.start_date.strftime('%b %d, %Y')} - {self.end_date.strftime('%b %d, %Y')}'")
        self.get_clients()

        if self.clients:
            log_message(f"{len(self.clients)} clients will be processed")
        else:
            self.warning_messages.append("No clients found for processing in current date range")
            log_message(f"No clients found for processing")

        client: Client
        for client in self.clients:
            try:
                log_message(f"---------------{client.full_name} (id-{client.id})---------------------")
                invoice_id = self.create_client_invoice(client.id)
                client.status.invoice_printed = True

                log_message(f"Configure and generate Invoice №{invoice_id}")
                resource_id = self.prepare_invoice_for_download(invoice_id)

                log_message(f"Download invoice (resource - {resource_id})")
                file_name = f"{client.first_name[:2]}{client.last_name[:2]}_{invoice_id}.pdf"
                path_to_file = os.path.join(TEMP_FOLDER, file_name)
                self._download_invoice(resource_id, path_to_file=path_to_file)

                log_message(f"Save '{os.path.basename(path_to_file)}' to Google Drive")
                g_drive = GoogleDrive(BOT_ACCOUNT)
                folder_id = g_drive.get_or_create_curr_month_folder(folder_id='1lzuHYw7OFyOk7Y9OBWjNkFuJAn9tnfmK')
                g_drive.create_file_in_folder(path_to_file, folder_id, file_name=os.path.basename(path_to_file))
                client.status.invoice_saved_to_folder = True

                self.send_invoice_to_client(client, path_to_file)
                client.status.email_sent = True

                os.remove(path_to_file)
            except ScheduledMaintenanceException as ex:
                raise ex
            except Exception as ex:
                log_message(f"Catch exception: {str(ex)}")
