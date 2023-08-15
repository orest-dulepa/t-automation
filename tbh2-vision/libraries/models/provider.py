import datetime
import re


class Provider:
    providers: dict = {}

    def __init__(self, provider_name: str, provider_id: str):
        self.provider_name: str = provider_name
        self.provider_id: str = provider_id
        self.tags: list = []
        self.full_location_info: str = ''

        # rates[payor][service_code] = rate
        self.rates: dict = {}

        # credentials_mapping[payor] = ['payor_short_name']
        self.credentials_mapping: dict = {}

        # credentials[payor_short_name] = [{'effective': datetime, 'expires': datetime}]
        self.credentials: dict = {}

        self.providers[provider_id] = self

    def does_credentials_available(self, payor: str) -> bool:
        if payor in self.credentials_mapping:
            return True
        return False

    def does_credentials_valid(self, payor: str, date_of_service: datetime) -> bool:
        count_of_valid: int = 0
        for short_name in self.credentials_mapping[payor]:
            if self.credentials[short_name]['start_date'] <= date_of_service <= self.credentials[short_name]['end_date']:
                count_of_valid += 1
        if count_of_valid >= len(self.credentials_mapping[payor]):
            return True
        return False
