from libraries import common
from urllib.parse import urlparse
import requests
import json
from lxml import html
import base64


class DomoAPI:
    def __init__(self, credentials: dict):
        self.url: str = credentials['url']
        self.login: str = credentials['login']
        self.password: str = credentials['password']
        self.is_site_available: bool = False
        self.base_url: str = self._get_base_url()
        self.cookies = self._get_auth_cookie()

    def _get_base_url(self):
        parsed_uri = urlparse(self.url)
        base_url: str = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return base_url

    def _get_auth_cookie(self):
        auth_url: str = f'{self.base_url}api/domoweb/auth/login'

        # Mandatory header without which the request will not work
        headers: dict = {
            'Content-Type': 'application/json;charset=UTF-8',
        }

        data: dict = {
            'username': self.login,
            'password': base64.b64encode(self.password.encode()).decode("utf-8"),
            'nocookie': True,
            'base64': True,
            'locale': 'en-US'
        }

        response = requests.post(auth_url, data=json.dumps(data), headers=headers)
        if response.status_code != 200:
            common.log_message('DOMO site is not available via web requests', 'ERROR')
            exit(1)
        return response.cookies

    def get_page_id_by_title(self, title: str) -> str:
        page_id: str = ''
        url: str = f'{self.base_url}api/domoweb/bootstrap?v2Navigation=true'

        response = requests.get(url, cookies=self.cookies)
        response_obj = json.loads(response.text)
        for page in response_obj['data']['pages']:
            if page['title'].strip().lower() == title.strip().lower():
                page_id = page['id'].strip()
        return page_id

    def get_drill_path_urns(self, page_id: str) -> list:
        url: str = f'{self.base_url}api/content/v3/stacks/{page_id}/cards?parts=drillPathURNs'

        response = requests.get(url, cookies=self.cookies)
        response_obj = json.loads(response.text)
        drill_path_urns: list = response_obj['cards'][0]['drillPathURNs']

        return drill_path_urns

    def get_urn_title(self, title: str, drill_path_urns: list) -> str:
        urn: str = ''
        url: str = f'{self.base_url}api/content/v1/cards?urns={",".join(drill_path_urns)}&parts=slicers,datasources'

        response = requests.get(url, cookies=self.cookies)
        response_obj = json.loads(response.text)
        for item in response_obj:
            if item['title'].strip().lower() == title.strip().lower():
                urn = item['urn']
        return urn

    def get_client_data_by_client_id(self, client_id: str, urn: str) -> dict:
        url: str = f'{self.base_url}api/content/v1/cards/kpi/{urn}/render?parts=graph,summary,annotations'

        # Mandatory header without which the request will not work
        headers: dict = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Referer': self.base_url,
        }
        data: dict = {
            "queryOverrides": {
                "filters": [
                    {
                        "label": "clientid",
                        "column": "clientid",
                        "operand": "EQUALS",
                        "values": [
                            client_id
                        ],
                        "dataSourceId": "9dc739d3-277c-41c5-b096-740e1cd75bc2",
                        "dataType": "numeric"
                    }
                ],
                "dataControlContext": {
                    "filterGroupIds": []
                },
                "overrideSlicers": True,
                "overrideDateRange": True
            },
            "chartState": {},
            "width": 960,
            "height": 400,
            "scale": 1
        }
        response = requests.put(url, headers=headers, data=json.dumps(data), cookies=self.cookies)
        response_obj = json.loads(response.text)
        return self.parse_table(client_id, response_obj['html'])

    @staticmethod
    def parse_table(client_id: str, html_table: str) -> dict:
        doc = html.fromstring(html_table)
        tr_elements = doc.xpath('//tr')
        index_client_id: int = -1
        index_lastcopayinvoiceid: int = -1
        index_lastcopayinvoicedate: int = -1
        index_copayowed: int = -1

        for col in tr_elements[0]:
            column_text: str = str(col.text_content()).strip().lower()
            if column_text == 'clientid' and index_client_id == -1:
                index_client_id = tr_elements[0].index(col)
            elif column_text == 'copayowed' and index_copayowed == -1:
                index_copayowed = tr_elements[0].index(col)
            elif 'invoice' in column_text and 'link' in column_text and index_lastcopayinvoiceid == -1:
                index_lastcopayinvoiceid = tr_elements[0].index(col)
            elif column_text == 'lastcopayinvoicedate' and index_lastcopayinvoicedate == -1:
                index_lastcopayinvoicedate = tr_elements[0].index(col)

        invoices: dict = {}
        empty_rows: int = 0
        for col in tr_elements[1:]:
            client_id_temp: str = str(col[index_client_id].text_content()).strip()
            if client_id_temp != client_id:
                common.log_message('The client ID does not match the DOMO site')
                exit(1)
            lastcopayinvoiceid: str = str(col[index_lastcopayinvoiceid].text_content()).strip()
            if not lastcopayinvoiceid or lastcopayinvoiceid == '0':
                empty_rows += 1
                continue
            lastcopayinvoicedate: str = str(col[index_lastcopayinvoicedate].text_content()).strip()
            copayowed: str = str(col[index_copayowed].text_content()).strip()

            invoices[lastcopayinvoiceid] = {
                                'amount': copayowed,
                                'date': lastcopayinvoicedate
                            }
        if empty_rows > 0:
            common.log_message('The table in DOMO contains {} record without invoice number'.format(empty_rows), 'INFO')
        if len(invoices.keys()) == 0:
            common.log_message(f'Unable to find {client_id} in DOMO, please check to determine whether a balance is still outstanding.', 'ERROR')
            exit(0)
        return invoices

    def get_invoices_info(self, client_id: str) -> dict:
        page_id: str = self.get_page_id_by_title('Shared')
        drill_path_urns: list = self.get_drill_path_urns(page_id)
        urn: str = self.get_urn_title('Amount Owed by Invoice', drill_path_urns)
        invoices: dict = self.get_client_data_by_client_id(client_id, urn)

        return invoices
