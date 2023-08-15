

class PaidClaim:
    def __init__(self, paid_claim_json: dict):
        self.id = paid_claim_json['claimId']
        self.client_id = paid_claim_json['clientId']
        self._client_first_name = paid_claim_json.get('clientFirstName', '').strip()
        self._client_last_name = paid_claim_json.get('clientLastName', '').strip()
        self.lines = []
        if self._client_first_name and self._client_last_name:
            self.name = f"{self._client_first_name[0]}.{self._client_last_name} - {self.id}"
        else:
            self.name = self.id

    def is_client_not_found(self):
        # JS analogue in https://members.centralreach.com/dist/static/js/claims/payments/models/PaidClaim.ts
        # get orphanedErrorMessage()
        if not self.client_id:
            return True
        return False

    def __repr__(self):
        return f"{self.name}"
