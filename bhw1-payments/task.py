import os
from datetime import datetime
from time import sleep

from libraries import common as com
from libraries.invoice import Invoice
from libraries.clients import Clients
from libraries.google_drive import GDrive
from libraries.gmail_service import Gmail
from libraries.central_reach import CentralReach
from libraries.report import Report
from libraries.exceptions import (
    MissingClient,
    DuplicatedClient,
    NoCRResults,
    NoBulkApply,
    EmptyGDrive,
)

from config import (
    BITWARDEN_DATA,
    CHECK_NUMBER,
    CHECK_DATE,
    INVOICE_FILE,
    EMAIL_RECIPIENT,
    BOT_MODE,
)


def main():
    """
    Main function which calls all other functions.
    """
    report = Report()

    date = str(datetime.today().strftime("%b-%d-%Y"))
    com.log_message("Start - Behavioral Healthworks Payments")
    com.print_version()

    com.log_message("\nEXECUTION ARGUMENTS\n")
    com.log_message(CHECK_NUMBER)
    com.log_message(CHECK_DATE)
    com.log_message(EMAIL_RECIPIENT)
    com.log_message(INVOICE_FILE)
    com.log_message(BOT_MODE)

    com.create_output_dir()

    com.log_message("\nDRIVE\n")
    try:
        gd = GDrive()
        gd.download_invoice_files(CHECK_NUMBER)
    except EmptyGDrive as e:
        com.log_message("Invalid check number: '{}'! {}".format(CHECK_NUMBER, str(e)))
        return

    com.log_message("\nCLIENTS DATA\n")
    cr = CentralReach(BITWARDEN_DATA["cr"])
    clients = Clients(cr.export_csv_contacts_file())

    com.log_message("\nINVOICE\n")
    for invoice_file in gd.invoice_file_names:
        if (
            INVOICE_FILE
            and INVOICE_FILE.upper() != "ALL"
            and INVOICE_FILE != invoice_file["title"]
        ):
            continue
        com.log_message(
            "Processing invoice file {} ...\n".format(invoice_file["title"])
        )

        try:
            invoice = Invoice("output/{}".format(invoice_file["title"]))
        except KeyError:
            com.log_message("Unknown invoice format or incorrect column names!")
            report.add_data(
                [
                    {
                        "failure_reason": "Incorrect Invoice file",
                        "invoice_file": invoice_file["title"],
                    }
                ]
            )
            continue

        com.log_message(invoice.df)
        for client_name in invoice.unique_client_names:
            com.log_message("\n")
            com.log_message("#######################################################")
            com.log_message("\n")
            com.log_message("CLIENT: {}".format(client_name))
            try:
                rows_invoice_not_cr = None
                rows_cr_not_invoice = None
                rows_amount_mismatch = None
                payor_mismatch = None

                client_id = clients.get_client_id(client_name)
                com.log_message("CLIENT_ID: {}".format(client_id))

                service_dates = invoice.get_service_date(client_name)
                com.log_message("INVOICE DATES: {}".format(service_dates))

                rows_number = invoice.get_rows_number(client_name)
                com.log_message("INVOICE ROWS NUMBER: {}".format(rows_number))

                total_payment = invoice.get_total_payment(client_name)
                com.log_message("INVOICE TOTAL PAYMENTS: {}".format(total_payment))

                apply_payment = invoice.get_apply_payment(client_name)
                com.log_message("INVOICE APPLY PAYMENTS: {}".format(apply_payment))

                res = False
                while not res:
                    cr.filter_billing_data(
                        service_dates[0],
                        service_dates[-1],
                        client_id,
                        invoice.invoice_type,
                    )
                    cr.filter_hide_headers()
                    cr.filter_check_rows_number(rows_number)
                    rows_invoice_not_cr = [
                        {
                            "failure_reason": "Row in Invoice but not in CR",
                            "invoice_file": invoice_file["title"],
                            "client_name": client_name,
                            "service_date": p[0].strftime("%-m/%d/%y"),
                            "cpt_code": p[1],
                            "expected_data": float(p[2]),
                        }
                        for p in cr.select_invoice_rows(apply_payment)
                    ]
                    rows_cr_not_invoice = [
                        {
                            "failure_reason": "Row in CR but not in Invoice",
                            "invoice_file": invoice_file["title"],
                            "client_name": client_name,
                            "service_date": p[0],
                            "cpt_code": p[1].split(":")[0],
                        }
                        for p in cr.get_rows_cr_not_invoice()
                    ]
                    cr.filter_show_headers()
                    cr.click_bulk_apply()
                    cr.bulk_hide_headers()
                    cr.bulk_check_total(total_payment)
                    res = cr.bulk_check_rows_number()

                rows_amount_mismatch = [
                    {
                        "failure_reason": "Amount mismatch Invoice vs CR",
                        "invoice_file": invoice_file["title"],
                        "client_name": client_name,
                        "service_date": p[0][0].strftime("%-m/%d/%y"),
                        "cpt_code": p[0][1],
                        "expected_data": float(p[0][2]),
                        "actual_data": float(p[1]),
                    }
                    for p in cr.bulk_apply_payments(apply_payment)
                ]

                payor_mismatch = [
                    {
                        "failure_reason": "Payor mismatch",
                        "invoice_file": invoice_file["title"],
                        "client_name": client_name,
                        "expected_data": p[0],
                        "actual_data": p[1],
                    }
                    for p in cr.bulk_finish_payment(
                        CHECK_DATE, CHECK_NUMBER, invoice.invoice_type
                    )
                ]

            except DuplicatedClient:
                com.log_message("DUPLICATED CLIENT FULLNAME!")
                report.add_data(
                    [
                        {
                            "failure_reason": "Duplicated client in CR",
                            "invoice_file": invoice_file["title"],
                            "client_name": client_name,
                        }
                    ]
                )
                continue

            except MissingClient:
                com.log_message("CLIENT_ID: N/A!")
                report.add_data(
                    [
                        {
                            "failure_reason": "Missing client in CR",
                            "invoice_file": invoice_file["title"],
                            "client_name": client_name,
                        }
                    ]
                )
                continue

            except NoCRResults:
                com.log_message("NO RESULTS IN CR!")
                report.add_data(
                    [
                        {
                            "failure_reason": "No search results in CR",
                            "invoice_file": invoice_file["title"],
                            "client_name": client_name,
                        }
                    ]
                )
                continue

            except NoBulkApply:
                com.log_message(
                    "Bulk Apply Button is unavailable! Probably cause no rows have been selected"
                )
                report.add_data(
                    [
                        {
                            "failure_reason": "Bulk Apply button not available in CR",
                            "invoice_file": invoice_file["title"],
                            "client_name": client_name,
                        }
                    ]
                )
                continue

            except Exception as e:
                com.log_message("Unknown error: {}".format(str(e)))
                report.add_data(
                    [
                        {
                            "failure_reason": "Unknown error",
                            "invoice_file": invoice_file["title"],
                            "client_name": client_name,
                        }
                    ]
                )
                continue

            finally:
                report.add_data(rows_invoice_not_cr)
                report.add_data(rows_cr_not_invoice)
                report.add_data(rows_amount_mismatch)
                report.add_data(payor_mismatch)

    report.create_report_file()

    try:
        gmail = Gmail()
        gmail.send_message(
            to=EMAIL_RECIPIENT,
            subject="ESSC/BHPN EOB's Report - Open Items",
            html_body="<p>Hi!<br>There are open items that need addressing in the attached report from the ESSC/BHPN Bot's latest run<br><br>Regards,<br>TA's ESSC/BHPN Bot</p>",
            attachments=(os.path.abspath("output/report.csv"),),
        )
        com.log_message(f"\nSent report to {EMAIL_RECIPIENT}")
    except Exception as ex:
        com.log_message(
            f"An error occurred while sending the letter, the body of the letter will be saved in outputs\n"
            f"{str(ex)}",
            "ERROR",
        )

    com.log_message("\n100% task - Bot has completed its task", "INFO")
    com.log_message("End - Behavioral Healthworks Payments")


if __name__ == "__main__":
    main()
