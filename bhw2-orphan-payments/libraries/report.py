import os
from collections import defaultdict


class PaymentIdProcessInfo:
    def __init__(self, payment_id):
        self.status = 'not changed'
        self.id = payment_id
        self.reconciled_pages = []
        self.page_in_progress = None
        # {claim: [(claim_line: count of billing entries)]}
        self.applied_claims = defaultdict(list)

    def start_page_progress(self, page: int):
        self.status = 'in process'
        self.page_in_progress = page

    def complete_page(self, page: int):
        self.status = 'complete'
        self.reconciled_pages.append(page)
        self.page_in_progress = None
        self.applied_claims.clear()

    def apply_claim_line(self, claim, claim_line):
        self.applied_claims[claim].append(claim_line)


class Report:

    def __init__(self):
        # {payment_id: {page: {claim_name: count}}}
        self.__voided_payments = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        # {payment_id: {page: {claim_name: [(claim_line: error_message)]}}}
        self.__undefined_claim_lines = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        # [(payment_id, reconciled_status)]
        self.__not_fully = []
        # {payment_id: {page: {claim_id: [claim_line]}}}
        self.__applied_but_not_reconcile = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self.payments_process_info = []
        self.__warning_messages = []

    def __get_process_info(self, payment_id) -> PaymentIdProcessInfo:
        return [p_i for p_i in self.payments_process_info if p_i.id == payment_id][0]

    def add_warning_message(self, message):
        self.__warning_messages.append(message)

    def add_applied_but_not_reconcile(self, payment_id, page, claim, claim_line):
        self.__applied_but_not_reconcile[payment_id][page][claim].append(claim_line)

    def add_payment_process(self, payment_id):
        self.payments_process_info.append(PaymentIdProcessInfo(payment_id))

    def start_payment_page_process(self, payment_id, page: int):
        process_info: PaymentIdProcessInfo = self.__get_process_info(payment_id)
        process_info.start_page_progress(page)

    def add_applied_claim_line(self, payment_id, claim_id, claim_line):
        process_info: PaymentIdProcessInfo = self.__get_process_info(payment_id)
        process_info.apply_claim_line(claim_id, claim_line)

    def add_completed_payment_page(self, payment_id, page: int):
        process_info: PaymentIdProcessInfo = self.__get_process_info(payment_id)
        process_info.complete_page(page)

    def add_undefined_claim_line(self, payment_id, page, claim, claim_line='', message='Undefined'):
        self.__undefined_claim_lines[payment_id][page][claim].append((claim_line, message))

    def add_voided_payment(self, payment_id, page, claim):
        self.__voided_payments[payment_id][page][claim] += 1

    def add_not_fully(self, payment_id, status):
        self.__not_fully.append((payment_id, status))

    def __is_all_payments_reconciled(self) -> bool:
        for payment_process_info in self.payments_process_info:
            if payment_process_info.status != 'complete':
                return False
        return True

    def __get_not_fully_payments_table(self) -> str:
        title = p('These payment IDs do not have a Reconciliation Status of "Fully" - Please Review')
        header = thead(tr(th('№') + th('Payment ID') + th('Reconcile Status')))
        rows = []
        idx = 1
        for payment_id, status in self.__not_fully:
            rows.append(tr(td(idx) + td(payment_id) + td(status)))
            idx += 1
        return title + table(header + tbody(''.join(rows)))

    def __get_voided_payments_table(self) -> str:
        title = p("These claim lines have voided payments ❗️ (They’ve been skipped & require attention)")
        header = thead(th('№') + th('Payment ID') + th('Page №') + th('Claim') + th('Voided Count'))
        rows = []
        idx = 1
        for payment_id, payments_dict in self.__voided_payments.items():
            for page, page_dict in payments_dict.items():
                for claim, voided_count in page_dict.items():
                    rows.append(tr(td(idx) + td(payment_id) + td(page) + td(claim) + td(voided_count)))
                    payment_id = '-----'
                    page = '-'
                    idx += 1
        return title + table(header + tbody(''.join(rows)))

    def __get_applied_but_not_reconcile_table(self) -> str:
        title = p(f"These claim lines were applied but not reconciled (require attention)")
        header = thead(tr(th('№') + th('Payment ID') + th('Page №') + th('Claim') + th('Claim line')))
        rows = ''
        idx = 1
        for payment_id, payment_dict in self.__applied_but_not_reconcile.items():
            for page, page_dict in payment_dict.items():
                for claim, claim_lines in page_dict.items():
                    for claim_line in claim_lines:
                        rows += (tr(td(idx) + td(payment_id) + td(page) + td(claim) + td(claim_line)))
                        payment_id = '-----'
                        page = '-'
                        claim = '-------'
                        idx += 1

        return title + table(header + tbody(rows))

    def __get_processed_payments_info_table(self) -> str:
        title = p(f"This is an overview of the bot’s scheduled run. Check status to see where it left off")
        not_completed_tables = []
        header = thead(tr(th('№') + th('Payment ID') + th('Reconciled pages') + th('Status')))
        rows = []
        for idx, payment_info in enumerate(self.payments_process_info):
            if payment_info.reconciled_pages:
                reconciled_pages = ', '.join(map(str, payment_info.reconciled_pages))
            else:
                reconciled_pages = '-'
            rows.append(tr(td(idx + 1) + td(payment_info.id) + td(reconciled_pages) + td(payment_info.status)))

            if payment_info.applied_claims:
                not_completed_table = self.__get_not_processed_payment_table(payment_info)
                not_completed_tables.append(not_completed_table)

        return title + table(header + tbody(''.join(rows))) + ''.join(not_completed_tables)

    @staticmethod
    def __get_not_processed_payment_table(payment_info: PaymentIdProcessInfo) -> str:
        title = p(f"Payment - {payment_info.id} was not complete fully, on page {payment_info.page_in_progress} "
                  f"was applied billing entries of next claims")
        header = thead(tr(th('№') + th('Claim') + th('Claim line')))
        rows = []
        idx = 1
        for claim, claim_lines_list in payment_info.applied_claims.items():
            for claim_line in claim_lines_list:
                rows.append(tr(td(idx) + td(claim) + td(claim_line)))
                claim = '-------'
                idx += 1

        return title + table(header + tbody(''.join(rows)))

    def __get_undefined_claim_lines_table(self) -> str:
        title = p("These claim lines are undefined and cannot be processed")
        header = thead(th('№') + th('Payment ID') + th('Page №') + th('Claim') + th('Claim Line') + th('Error message'))
        rows = []
        idx = 1
        for payment_id, payments_dict in self.__undefined_claim_lines.items():
            for page, page_dict in payments_dict.items():
                for claim, lines_messages_list in page_dict.items():
                    for claim_line, message in lines_messages_list:
                        rows.append(tr(td(idx) + td(payment_id) + td(page) + td(claim) + td(claim_line) + td(message)))
                        payment_id = '-----'
                        page = '-'
                        claim = '-'
                        idx += 1
        return title + table(header + tbody(''.join(rows)))

    def __get_warning_messages_html(self) -> str:
        return f'<br><div class="warning">Note!<br>{"<br>".join(self.__warning_messages)}</div></div><br>'

    def get_report_in_html(self) -> str:
        html_body = ''

        if self.__not_fully:
            html_body += self.__get_not_fully_payments_table()

        if self.__voided_payments:
            html_body += self.__get_voided_payments_table()

        if self.__applied_but_not_reconcile:
            html_body += self.__get_applied_but_not_reconcile_table()

        if self.__undefined_claim_lines:
            html_body += self.__get_undefined_claim_lines_table()

        if not self.__is_all_payments_reconciled():
            html_body += self.__get_processed_payments_info_table()

        if self.__warning_messages:
            html_body += self.__get_warning_messages_html()

        if html_body:
            with open(os.path.abspath('libraries/mail/style.css'), 'r') as f:
                style = f.read()
            start_body = "Hello,<br>There are some payments that need to be manually verified." + img_think_emoji()
            end_body = "<br>Regards,<br>Orphan Payments Bot"
            body_html = body(f'{start_body}{html_body}{img_ta()}{end_body}')
            html_body = f'<head><style>{style}</style></head>{body_html}'
            return html_body
        return ''


def body(s):
    return f'<body style="color:#333; font:100%/30px Arial, sans-serif; font-weight:550; line-height:1.7">{s}</body>'


def table(s):
    return f'<table>{s}</table>'


def td(s):
    return f'<td>{s}</td>'


def tr(s):
    return f'<tr>{s}</tr>'


def th(s):
    return f'<th>{s}</th>'


def thead(s):
    return f'<thead>{s}</thead>'


def tbody(s):
    return f'<tbody>{s}</tbody>'


def p(s):
    return f'<p>{s}</p>'


def img_think_emoji():
    return '<img src="cid:emj.jpg" alt="" style="display:block; margin:5px auto; width:100px">'


def img_ta():
    return '<img src="cid:ta.jpg" alt="" style="float:right; width:70px">'
