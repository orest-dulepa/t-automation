import datetime
import re


class Insurance:

    def __init__(self, payer_name: str, valid_from: datetime, valid_to: datetime, is_primary: bool):
        self.payer_name: str = payer_name
        # Primary or Secondary
        self.is_primary = is_primary

        self.valid_from: datetime = valid_from
        self.valid_to: datetime = valid_to

        self.address: str = ''
        self.payer_id: str = ''

        self.subscriber_first_name: str = ''
        self.subscriber_last_name: str = ''
        self.subscriber_middle_name: str = ''
        self.subscriber_gender: str = ''
        self.subscriber_address: str = ''
        self.subscriber_dob: str = ''
        self.subscriber_id: str = ''
