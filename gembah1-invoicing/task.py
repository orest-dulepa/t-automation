import os
import traceback
import sys
import datetime

from RPA.Robocloud.Secrets import Secrets
from libraries.common import log_message, print_version
from ta_bitwarden_cli.ta_bitwarden_cli import Bitwarden
from libraries.slack_bot import SlackBot
from libraries.quickbooks import Quickbooks
from config import CREDENTIALS_NAME, TEMP_FOLDER, OUTPUT_FOLDER, PROD


CREDENTIALS = {
    'example': {'login': '', 'password': '', 'url': '', 'otp': ''}
}


def get_bitwarden_credentials(credentials_name: str = 'bitwarden_credentials') -> dict:
    secrets = Secrets()
    bitwarden_credentials = secrets.get_secret(credentials_name)

    return bitwarden_credentials


def main():
    log_message('Start Invoicing - Gembah')
    print_version()

    if not OUTPUT_FOLDER:
        os.mkdir(OUTPUT_FOLDER)
    if not TEMP_FOLDER:
        os.mkdir(TEMP_FOLDER)

    global CREDENTIALS
    bw = Bitwarden(get_bitwarden_credentials())
    CREDENTIALS = bw.get_credentials(CREDENTIALS_NAME)

    log_message('Logging In')
    quickbooks: Quickbooks = Quickbooks(
        CREDENTIALS['quickbooks']['login'],
        CREDENTIALS['quickbooks']['password'],
        CREDENTIALS['quickbooks']['url']
    )

    if PROD:
        quickbooks.slack = SlackBot(CREDENTIALS['slack']['token'], CREDENTIALS['slack']['channel_invoicing'])
    else:
        print('Dev run')
        quickbooks.slack = SlackBot(CREDENTIALS['slack']['token_ta'], CREDENTIALS['slack']['channel_invoicing_ta'])

    quickbooks.slack.manager = CREDENTIALS['slack']['manager_name']
    rows: list = quickbooks.sheets.get_sheet_data(CREDENTIALS['slack']['spreadsheet_id'])
    # update columns name
    columns: list = rows[0]
    for i in range(len(columns)):
        columns[i] = str(columns[i]).strip().lower()

    log_message('Data from "AM Bot Template- Clean" received')
    if not quickbooks.login_to_site():
        log_message('Unable to log in to Quickbooks', 'INFO')
        exit(0)
    quickbooks.go_to_client_page()
    for row in rows[1:]:
        try:
            if len(row) < 6:
                print(f'Not enough data. Row index {rows.index(row) + 1}')
                continue
            if not row[columns.index('account')] or not row[columns.index('service type')] \
                    or not row[columns.index('amount')]:
                print(f'Empty mandatory column. Row index {rows.index(row) + 1}')
                quickbooks.sheets.write_to_sheet('invoice uploaded', rows.index(row) + 1, 'No')
                continue
            if len(row) > columns.index('invoice uploaded'):
                if str(row[columns.index('invoice uploaded')]).strip().lower() == 'yes':
                    continue

            log_message(f'Start processing the {row[columns.index("account")]} account', 'INFO')
            success: bool = quickbooks.add_invoice(
                customer=row[columns.index('account')],
                service=row[columns.index('service type')],
                description=row[columns.index('description')],
                rate=float(str(row[columns.index('amount')]).replace('$', '').replace(',', '')),
                processing_fee=True if str(row[columns.index('3% markup')]).strip().lower() == 'yes' else False,
            )
            if success:
                quickbooks.sheets.write_to_sheet('invoice uploaded', rows.index(row) + 1, 'Yes')
                quickbooks.slack.send_message(
                    f"{quickbooks.slack.get_user_tag(row[columns.index('account manager')])} - {row[columns.index('account')]} Invoice of {row[columns.index('amount')]} has been uploaded to Quickbooks"
                )
            else:
                quickbooks.sheets.write_to_sheet('invoice uploaded', rows.index(row) + 1, 'No')
        except Exception as ex:
            log_message(f'Processing error. Row index {rows.index(row) + 1}. {str(ex)}')

            quickbooks.browser.take_screenshot(
                os.path.join(
                    OUTPUT_FOLDER,
                    f'Element_not_available_{datetime.datetime.now().strftime("%H_%M_%S")}.png'
                )
            )
            quickbooks.login_to_site()
            quickbooks.go_to_client_page()
    quickbooks.check_paid(rows, columns)
    log_message('End Invoicing - Gembah')


if __name__ == '__main__':
    main()
