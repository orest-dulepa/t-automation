import re
import uuid
from collections import defaultdict
from datetime import datetime

from libraries.billing_entry import BillingEntry
from libraries.claim_line import ClaimLine
from libraries.common import log_message
from libraries.paid_claim import PaidClaim
from libraries.report import Report
from libraries.central_reach_requests import CentralReachRequests
from libraries.utils import ScheduledMaintenanceException


class CentralReach(CentralReachRequests):
    # Parameters for Test runs (if all False - nothing will be changed in Central Reach site, but logs will be writen)
    is_remove_combined = True
    is_apply = True
    is_reconcile = True

    def __init__(self, credentials: dict):
        """ Create session and login to "Central Reach" site
        :param credentials: dict with keys "login" and "password"
        """
        super().__init__()
        self.login: str = 'OPayments'
        self.password: str = credentials['OPayments']
        self.report: Report = Report()
        self._login_to_central_reach(self.login, self.password)

    @staticmethod
    def __get_guid() -> str:
        return str(uuid.uuid4())

    @classmethod
    def __create_payment_json(cls, bill_entry_id: int, claim_line: ClaimLine, reference: str) -> dict:
        """ Prepare dictionary for Orphaned claim line reconciliation post request """
        payment = {
            "billingEntryId": bill_entry_id,
            "date": claim_line.reconcile_date_str,
            "paymentType": claim_line.payment_type,
            "reference": reference,
            "amount": claim_line.reconcile_amount,
            "claimLineId": claim_line.id,
            "claimEntryItemId": claim_line.entry_item_id,
            "notes": claim_line.notes,
            "paymentLabels": claim_line.payment_labels,
            "payorId": claim_line.payor_id,
            "manual": claim_line.manual,
            "reconClonedPayment": claim_line.recon_cloned_payment,
            "guid": cls.__get_guid(),
            "reconAdjustCopay": False,
        }
        return payment

    @classmethod
    def __create_service_line_payment_json(cls, claim_line: ClaimLine, reference: str) -> dict:
        """ Prepare dictionary for Service Line Adjustments claim line reconciliation post request """
        service_line_payment = {
            "billingEntryId": claim_line.billing_entry_id,
            "date": claim_line.reconcile_date_str,
            "paymentType": claim_line.payment_type,
            "reference": reference,
            "amount": claim_line.reconcile_amount,
            "claimLineId": claim_line.id,
            "claimLineAdjId": claim_line.claim_line_adj_id,
            "claimEntryItemId": claim_line.entry_item_id,
            "notes": claim_line.notes,
            "paymentLabels": claim_line.payment_labels,
            "payorId": claim_line.payor_id,
            "manual": claim_line.manual,
            "reconClonedPayment": claim_line.recon_cloned_payment,
            "guid": cls.__get_guid(),
            "reconAdjustCopay": False,
        }
        if claim_line.relative_co is not None:
            service_line_payment["relativeCO"] = claim_line.relative_co
        return service_line_payment

    @staticmethod
    def __add_service_line_adjustments(page_claims: list, orphaned_payments_dict: dict) -> dict:
        """
        Populate data about applied claim lines with Service Line Adjustments for reconciliation
        :param paid_claims: list with dictionaries about each claim from site response
        :param orphaned_payments_dict: Dictionary with info about applied claim lines.
        :return: Dictionary with info about applied claim lines with service line adjustments.
        """
        all_payments_dict = orphaned_payments_dict
        service_lines_count = 0
        claim: PaidClaim
        for claim in page_claims:
            if claim.id not in all_payments_dict:
                continue
            claim_line: ClaimLine
            for claim_line in claim.lines:
                if claim_line.billing_entry_id not in all_payments_dict[claim.id]:
                    continue

                if claim_line.is_service_line_adjustment():
                    if claim_line.is_service_line_adjustment_checkbox_available():
                        if claim_line.adjustment_reason in ['1', '2', '3']:
                            all_payments_dict[claim.id][claim_line.billing_entry_id].append(claim_line)
                            service_lines_count += 1
        if service_lines_count:
            log_message(f"Add {service_lines_count} service line adjustments")
        return all_payments_dict

    def __reconcile_all(self, payments_dict: dict, claim_payment_check_number: str, payment_id: int, page: int) -> None:
        """
        This method prepare info about applied claim lines for request and send Post request for reconcile all of them
        :param payments_dict: Dictionary with info about applied claim lines.
                {'claim_id': {'billing_entry_id': ['payment', 'payment']}}
        :param claim_payment_check_number:
        :param payment_id: Current payment id
        :param page: Current page
        """
        payments_for_request = []
        for claim_id, billings_dict in payments_dict.items():
            for billing_entry_id, claim_lines in billings_dict.items():
                for claim_line in claim_lines:
                    if claim_line.is_orphaned() or claim_line.is_applied_but_not_reconcile():
                        json_payment = self.__create_payment_json(billing_entry_id, claim_line,
                                                                  reference=claim_payment_check_number)
                        payments_for_request.append(json_payment)
                    elif claim_line.is_service_line_adjustment():
                        json_payment = self.__create_service_line_payment_json(claim_line,
                                                                               reference=claim_payment_check_number)
                        payments_for_request.append(json_payment)
        try:
            if payments_for_request:
                if self.is_reconcile:
                    self._reconcile_all_post(payments=payments_for_request, payment_id=payment_id)
                log_message(f"Reconcile {len(payments_for_request)} payments")
            else:
                log_message(f"No claims for reconcile")
        except Exception as ex:
            log_message(f"Error occurred with reconcile {len(payments_for_request)} payments\n{str(ex)}", 'ERROR')
            for claim_id, billings_dict in payments_dict.items():
                for billing_entry_id, claim_lines in billings_dict.items():
                    for claim_line in claim_lines:
                        self.report.add_applied_but_not_reconcile(payment_id, page, claim_id, claim_line.name)
            if isinstance(ex, ScheduledMaintenanceException):
                raise ex

    def initial_payment_ids_check(self, payments_ids: list, start_date: datetime, end_date: datetime) -> list:
        """ This method search for ids  in Claims Era List, check is 'Reconciled status' not 'Fully' """
        payments_ids = list(set(map(int, payments_ids)))

        era_list = self._get_era_list(start_date, end_date)

        already_fully_ids = []
        payment_ids_for_processing = []

        for item in era_list['items']:
            if int(item['Id']) in payments_ids:
                if item['Reconciled'] == 'Fully':
                    already_fully_ids.append(item['Id'])
                else:
                    payment_ids_for_processing.append(item['Id'])

        unfounded_ids = [p_id for p_id in payments_ids if p_id not in payment_ids_for_processing + already_fully_ids]
        if unfounded_ids:
            warning_message = f"Era list in date range '{start_date.date()} - {end_date.date()}', " \
                              f"does not contain these payment IDs: {', '.join(map(str, unfounded_ids))}"
            log_message(warning_message, 'WARN')
            self.report.add_warning_message(warning_message)
        if already_fully_ids:
            log_message(f"Next payment IDs already has 'Fully' in 'Reconcile status' column and will not be processed: "
                        f"{', '.join(map(str, already_fully_ids))}")
        return payment_ids_for_processing

    def check_payment_ids_reconciled_status(self, payments_ids: list, start_date: datetime, end_date: datetime) -> None:
        """ This method iterate over Claims Era List and check 'Reconciled status' """
        log_message(f"Verify complete reconciliation of payments")
        try:
            era_list = self._get_era_list(start_date, end_date)
            not_fully_ids = []

            for item in era_list['items']:
                if int(item['Id']) in payments_ids and item['Reconciled'] != 'Fully':
                    not_fully_ids.append(item['Id'])
                    self.report.add_not_fully(item['Id'], item['Reconciled'])
            if not_fully_ids:
                log_message(f"This payment IDs has not 'Fully' in 'Reconcile status' column and need to be checked: "
                            f"{', '.join(map(str, not_fully_ids))} ", 'WARN')
        except Exception as ex:
            log_message(f"An error occurred while checking 'Reconciled status' of payments\n"
                        f"{str(ex)}", 'ERROR')

    def __get_billing_entry_id_for_apply(self, claim: PaidClaim, claim_line: ClaimLine) -> int:
        """ Get necessary billing entry id for current claim line """
        billing_entries_list = self._get_billing_entries(claim.client_id, claim_line.service_date)

        for billing_entry_json in billing_entries_list:
            bill_entry = BillingEntry(billing_entry_json)
            if claim_line.procedure_code == bill_entry.code:
                if claim_line.service_date.date() == bill_entry.date_from.date():
                    return bill_entry.id

    def __remove_combined_billing_entries(self, claims: list):
        combined_count = 0
        paid_claim: PaidClaim
        for paid_claim in claims:
            claim_line: ClaimLine
            for claim_line in paid_claim.lines:
                if claim_line.is_combined() and claim_line.is_applied_but_not_reconcile():
                    try:
                        if self.is_remove_combined:
                            self._remove_billing_entry_link(claim_line.id)
                        combined_count += 1
                    except ScheduledMaintenanceException as ex:
                        raise ex
                    except Exception as ex:
                        log_message(f"Error with removing combine entry link, claim {paid_claim.name}, "
                                    f"claim line {claim_line.name}. {str(ex)}")
        return combined_count

    def __get_claims(self, payment_id, page, log_errors=True):
        """
        Get all claims and them unique claim lines from page
        :param payment_id: current payment ID
        :param page: current page
        :param log_errors: False if you don't want log about wrong Claims (useful for not first page reading)
        :return: page_claims - list with PaidClaim objects
                 is_next_page - bool, is next page exist
                 check_number - page value for reconciling data
        """
        page_payments = self._get_payments(payment_id, page)
        is_next_page = page_payments['claimPayment']['hasNext']
        check_number = page_payments['claimPayment']['checkNumber']

        page_claims = []
        for paid_claim_json in page_payments['paidClaims']:
            try:
                paid_claim = PaidClaim(paid_claim_json)
            except Exception as ex:
                if log_errors:
                    log_message(f"Undefined claim line type. {str(ex)}")
                    self.report.add_undefined_claim_line(payment_id, page, 'Undefined',
                                                         message='Undefined claim payment')
                continue
            for claim_line_json in paid_claim_json['claimLines']:
                try:
                    claim_line = ClaimLine(claim_line_json)
                    # Collect first entries of Claim lines
                    if claim_line.id not in [claim_line.id for claim_line in paid_claim.lines]:
                        paid_claim.lines.append(claim_line)
                except Exception as ex:
                    if log_errors:
                        log_message(f"Undefined claim line type,  claim {paid_claim.name}. {str(ex)}")
                        self.report.add_undefined_claim_line(payment_id, page, paid_claim.name, claim_line='Undefined',
                                                             message='Undefined claim line')
            page_claims.append(paid_claim)
        return page_claims, is_next_page, check_number

    def __apply_billing_entries_for_orphaned(self, page_claims: list, payment_id: int, page: int) -> dict:
        """
        This method iterate over all claim lines, get necessary billing entries and apply billing entries for claim line
        :param page_claims: list with PaidClaim objects
        :param payment_id: Current payment id
        :param page: Current page
        :return: Dictionary with info about applied claim lines.
         Map structure {'claim_id': {'billing_entry_id': ['payment', 'payment']}}
        """
        payments_dict = defaultdict(lambda: defaultdict(list))

        already_applied_count = 0
        orphaned_count = 0
        paid_claim: PaidClaim
        for paid_claim in page_claims:
            claim_line: ClaimLine
            for claim_line in paid_claim.lines:
                if paid_claim.is_client_not_found():
                    self.report.add_undefined_claim_line(payment_id, page, paid_claim.name, claim_line.name,
                                                         message='Client not found.')
                elif claim_line.is_void_payment():
                    self.report.add_voided_payment(payment_id=payment_id, page=page, claim=paid_claim.name)
                elif claim_line.is_applied_but_not_reconcile():
                    already_applied_count += 1
                    payments_dict[paid_claim.id][claim_line.billing_entry_id].append(claim_line)
                elif claim_line.is_orphaned():
                    try:
                        bill_entry_id = self.__get_billing_entry_id_for_apply(paid_claim, claim_line)

                        if bill_entry_id:
                            payments_dict[paid_claim.id][bill_entry_id].append(claim_line)
                            if self.is_apply:
                                self._apply_billing_entries_changes(claim_line.id, [bill_entry_id])
                            self.report.add_applied_claim_line(payment_id, paid_claim.name, claim_line.name)
                            orphaned_count += 1
                    except ScheduledMaintenanceException as ex:
                        raise ex
                    except Exception as ex:
                        log_message(f"Error with claim line applying, claim {paid_claim.name}, "
                                    f"claim line {claim_line.name}. {str(ex)}")
                        server_messages = re.findall(r'(?<=\'message\': ")[^"]+', str(ex))
                        if server_messages:
                            self.report.add_undefined_claim_line(payment_id, page, paid_claim.name, claim_line.name,
                                                                 message=server_messages[0])
                        else:
                            self.report.add_undefined_claim_line(payment_id, page, paid_claim.name, claim_line.name)
        if orphaned_count:
            log_message(f"Applied {orphaned_count} Claim Lines.")
        if already_applied_count:
            log_message(f'Have already been applied {already_applied_count} Claim Lines')
        if not orphaned_count and not already_applied_count:
            log_message(f"No Claim Lines for applying")
        return payments_dict

    def process_payments_ids(self, payments_ids: list) -> None:
        """ This method iterate over each payment Id and processed each page """
        for payment_id in payments_ids:
            self.report.add_payment_process(payment_id)

        for payment_id in payments_ids:
            page_number = 1
            while True:
                log_message(f'-------------------Payment ID-{payment_id}-------Page-{page_number}-------------------')
                paid_claims, is_next_page, check_number = self.__get_claims(payment_id, page_number)
                # Remove already applied combined claim lines if they exist on page
                combined_count = self.__remove_combined_billing_entries(paid_claims)
                if combined_count:
                    log_message(f"Remove {combined_count} combined billing entry links")
                    # Update claims data if remove any billing entries
                    paid_claims, _, _ = self.__get_claims(payment_id, page_number, False)

                self.report.start_payment_page_process(payment_id=payment_id, page=page_number)

                # Identify Orphaned Payments & Select Billing Entries
                applied_payments = self.__apply_billing_entries_for_orphaned(paid_claims, payment_id, page_number)
                if applied_payments:
                    # Reviewing Service Line Adjustments
                    paid_claims, _, _ = self.__get_claims(payment_id, page_number, False)
                    all_payments_dict = self.__add_service_line_adjustments(paid_claims, applied_payments)

                    # Reconciling Payments
                    self.__reconcile_all(all_payments_dict, check_number, payment_id, page_number)
                self.report.add_completed_payment_page(payment_id=payment_id, page=page_number)

                if is_next_page:
                    page_number += 1
                else:
                    break
