import datetime
import re
from libraries.models.insurance import Insurance


class Client:
    # dict[client_id] = ClientObj
    clients: dict = {}

    def __init__(self, client_name: str, client_id: str):
        self.client_name: str = client_name
        self.client_id: str = client_id
        self.tags: list = []
        self.location: str = ''
        self.location_city: str = ''

        # list of Insurance obj
        self.insurances: list = []
        # self.secondary_insurances: list = []
        # self.primary_insurances: list = []
        self.is_insurance_details_scraped: bool = False

        self.clients[client_id] = self

    def get_insurance(self, insurance_name: str, insurance_type: str, date_from: str, date_to: str) -> Insurance:
        valid_from: datetime = datetime.datetime.strptime(date_from, '%m/%d/%Y')
        if date_to:
            valid_to: datetime = datetime.datetime.strptime(date_to, '%m/%d/%Y')
        else:
            valid_to: datetime = datetime.datetime.now()

        is_primary: bool = insurance_type == 'P'
        for insurance in self.insurances:
            if insurance_name == insurance.payer_name and insurance.is_primary == is_primary \
                    and insurance.valid_from == valid_from and insurance.valid_to.date() == valid_to.date():
                return insurance
