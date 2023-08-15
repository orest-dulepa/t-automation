import re
from datetime import datetime


class ClaimLine:
    def __init__(self, claim_line_json: dict):
        self.__json_data = claim_line_json
        self.id = self.__json_data['claimLineId']
        self.service_date_str = self.__json_data['serviceDate']
        self.service_date = self.get_service_date()
        self.reconcile_date_str = self.__json_data['reconcileDate']
        self.payment_type = self.__json_data['paymentType']
        self.reconcile_amount = self.__json_data['reconcileAmount']
        self.entry_item_id = self.__json_data['claimEntryItemId']
        self.payor_id = self.__json_data['payorId']
        self.manual = self.__json_data['manual']
        self.can_reconcile = self.__json_data['canReconcile']
        self.billing_entry_id = self.__json_data['billingEntryId']
        self.procedure_code = self.__json_data.get('procedureCode', '')
        self.procedure_code_qual = self.__json_data.get('procedureCodeQual', '')
        self.name = f'{self.procedure_code_qual} {self.procedure_code}'

        # For Claim line
        self.combined_header = self.__json_data.get('combinedHeader', None)
        self.void_warning = self.__json_data.get('voidWarning', None)
        self.ref_warning = self.__json_data.get('refWarning', None)
        self.recon_cloned_payment = False
        self.notes = self.__json_data.get('processedNote', '')
        self.payment_labels = self.__json_data.get('paymentLabels', '')
        if isinstance(self.payment_labels, list):
            self.payment_labels = ','.join(self.payment_labels)

        self.adjustment_type = self.__json_data.get('adjustmentType', '')
        if self.is_service_line_adjustment():
            self.adjustment_reason = str(self.__json_data.get('adjustmentReason', '')).strip()
            self.claim_line_adj_id = self.__json_data['claimLineAdjId']
            self.relative_co = self.__json_data.get('relativeCO', None)

    def get_service_date(self) -> datetime:
        search_res = re.search(r'(\d{4})-(\d{2})-(\d{2})', self.service_date_str)
        if search_res is None:
            raise Exception("Wrong format", search_res, self.service_date_str)

        year, month, day = search_res.groups()
        return datetime(int(year), int(month), int(day))

    def is_orphaned(self):
        # JS analogue in https://members.centralreach.com/dist/static/js/claims/payments/models/ClaimLine.ts
        # get isOrphaned()
        if not self.billing_entry_id and self.combined_header is False:
            return True
        return False

    def is_service_line_adjustment(self):
        # JS analogue in https://members.centralreach.com/dist/static/js/claims/payments/ClaimLineView.tsx
        # class ClaimLineView
        if self.adjustment_type == "Service Line":
            return True
        return False

    def is_service_line_adjustment_checkbox_available(self):
        # JS analogue in https://members.centralreach.com/dist/static/js/claims/payments/ClaimLineView.tsx
        # const ServiceLineAdjustmentRow
        if self.is_service_line_adjustment():
            if self.can_reconcile and self.billing_entry_id and self.combined_header is not False:
                return True
        return False

    def is_void_payment(self):
        # JS analogue in https://members.centralreach.com/dist/static/js/claims/payments/ClaimLineView.tsx
        # const HeaderRow, const LineRow
        if self.void_warning is not None and self.ref_warning is not None:
            if self.void_warning or self.ref_warning:
                return True
        return False

    def is_applied_but_not_reconcile(self):
        # JS analogue in https://members.centralreach.com/dist/static/js/claims/payments/ClaimLineView.tsx
        # const HeaderRow
        if not self.is_service_line_adjustment() and self.billing_entry_id:
            if self.billing_entry_id and not self.__json_data['reconcileCount']:
                return True
        return False

    def is_combined(self):
        if not self.is_service_line_adjustment() and self.combined_header:
            return True
        return False

    def remove_billing_entry(self):
        if self.is_combined():
            self.combined_header = False
            self.billing_entry_id = 0

    def __repr__(self):
        return f"{self.name}"
