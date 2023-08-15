import re


class ClientStatus:
    def __init__(self):
        self.email_sent = False
        self.invoice_printed = False
        self.invoice_saved_to_folder = False


class Client:
    def __init__(self, details_json: dict):
        self.id = details_json['Id']
        self.first_name = details_json['FirstName']
        self.last_name = details_json['LastName']
        self.full_name = details_json['FullName']

        email_value = details_json.get('Email', '')
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', email_value)
        if emails:
            self.email = emails[0]
            self.additional_emails = emails[1:]
        else:
            self.email = ''
            self.additional_emails = []

        self.status = ClientStatus()

    def __repr__(self):
        return f"{self.first_name}, {self.last_name} (ID: {self.id})"
