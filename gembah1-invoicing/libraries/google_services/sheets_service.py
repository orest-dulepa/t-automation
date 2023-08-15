from googleapiclient.discovery import build
from config import Account
from libraries.google_services.google_services import GoogleServices


class GoogleSheets(GoogleServices):
    columns: dict = {
        'date': 'A',
        'account': 'B',
        'sku': 'C',
        'service type': 'D',
        'description': 'E',
        '3% markup': 'F',
        'amount': 'G',
        'account manager': 'H',
        'invoice uploaded': 'I',
        'invoice paid': 'J',
        'amount paid': 'K',
        'invoice payment date': 'L',
    }
    spreadsheet_id = ''

    def __init__(self, account: Account):
        self.service = build('sheets', 'v4', credentials=self._get_credentials(account), cache_discovery=False)

    def get_sheet_data(self, spreadsheet_id: str) -> list:
        self.spreadsheet_id = spreadsheet_id
        data = self.service.spreadsheets().values().batchGet(
            spreadsheetId=spreadsheet_id,
            ranges="'AMBilling Invoice Requests'!A1:L1000"
        ).execute()
        rows: list = data['valueRanges'][0]['values']

        return rows

    def write_to_sheet(self, column_name: str, index_row: int, value: str) -> None:
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=self.columns[column_name.strip().lower()] + str(index_row),
            valueInputOption='USER_ENTERED',
            body={
                "values": [
                    [
                        value
                    ]
                ]
            }
        ).execute()
