import boto3
import sqlite3
import json
import random
import time
import sys
import traceback
from datetime import date
from os.path import join, basename
from libraries.google_services.drive_service import GoogleDrive
from libraries.common import log
from config import BOT_ACCOUNT, PROD, TEMP_FOLDER
from libraries.textract_parsing import TextractParsing
from libraries.invoice import InvoiceData


def lambda_handler(event, context):
    bucket_name: str = 'verisk1-dev'

    log('start')
    log('event')
    log(event)

    pdf_file_name: str = event['file_name']
    pdf_file_id: str = event['file_id']
    template_file_name: str = event['template_name']
    master_list_db: str = event['master_list_db']
    master_list_archive_db: str = event['master_list_archive_db']
    entered_folder_id: str = event['entered_folder_id']
    manual_folder_id: str = event['manual_folder_id']
    parent_folder_id: str = event['parent_folder_id']

    log(f'Start processing {pdf_file_name}')

    drive: GoogleDrive = GoogleDrive(BOT_ACCOUNT)
    pdf_file_path: str = drive.download_file_by_name(pdf_file_name, TEMP_FOLDER, pdf_file_id)

    items: list = []
    try:
        items = parse_pdf_via_textract(pdf_file_path, bucket_name)
    except Exception as ex:
        log(str(ex))
        try:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            del exc_info
        except Exception as ex:
            log(str(ex))
            pass

    if items:
        log('Download DB files')
        master_list_db_path: str = join(TEMP_FOLDER, master_list_db)
        master_list_archive_db_path: str = join(TEMP_FOLDER, master_list_archive_db)
        template_file_path: str = join(TEMP_FOLDER, template_file_name)

        # Get files from S3
        s3 = boto3.client('s3')
        s3.download_file(bucket_name, master_list_db, master_list_db_path)
        s3.download_file(bucket_name, master_list_archive_db, master_list_archive_db_path)
        s3.download_file(bucket_name, template_file_name, template_file_path)

        log('Try find unique id')
        try_find_unique_id(items, master_list_db_path)
        try_find_unique_id(items, master_list_archive_db_path)

        # Prepare result
        rows: list = []
        for i in items:
            item: InvoiceData = i
            if not item.lci_id:
                item.lci_id = 'Suspense'
            row: list = [
                item.case.lstrip('0'), item.lci_id, item.portfolio_id, item.true_owner, item.full_name,
                item.claim.lstrip('0'), item.last4digits, item.amount, item.trustee_last_name,
                item.check_number.lstrip('0'), item.check_date, item.check_owner,
                date.today().strftime("%m/%d/%Y"), item.putbacks
            ]
            rows.append(row)

        # Upload parsed DATA
        s3 = boto3.resource('s3')
        s3object = s3.Object(bucket_name, basename(pdf_file_path).replace('.pdf', '_parsed.json'))
        s3object.put(Body=(bytes(json.dumps(rows).encode('UTF-8'))))

        # Move file to processed folder
        drive.service.files().update(fileId=pdf_file_id, addParents=entered_folder_id,
                                     removeParents=parent_folder_id).execute()
    else:
        # Move file to folder for manual processing
        log('File cannot be parsed')
        # time.sleep(random.randint(1, 15))
        if not manual_folder_id:
            manual_folder_id = drive.get_or_create_folder('For manual processing', [], parent_folder_id, True)
        drive.service.files().update(fileId=pdf_file_id, addParents=manual_folder_id,
                                     removeParents=parent_folder_id).execute()

    return {
        'statusCode': 200,
        'body': json.dumps('end')
    }


def parse_pdf_via_tesseract(pdf_file_path: str):
    pass


def parse_pdf_via_textract(pdf_file_path: str, bucket_name: str) -> list:
    parsing_obj: TextractParsing = TextractParsing(pdf_file_path, bucket_name)
    parsing_obj.upload_file_to_s3()

    try:
        s3 = boto3.resource('s3')

        content_object = s3.Object(bucket_name, basename(pdf_file_path).replace('.pdf', '.json'))
        file_content = content_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)
        parsing_obj.blocks = json_content
    except Exception as ex:
        log(str(ex))
        parsing_obj.get_response_from_textract()

    # Remove temp file from bucket
    s3 = boto3.client('s3')
    s3.delete_object(Bucket=bucket_name, Key=parsing_obj.pdf_s3_file_name)

    # TODO - remove it - just for test
    s3 = boto3.resource('s3')
    s3object = s3.Object(bucket_name, basename(pdf_file_path).replace('.pdf', '.json'))
    s3object.put(Body=(bytes(json.dumps(parsing_obj.blocks).encode('UTF-8'))))

    items: list = parsing_obj.prepare_result()

    return items


def try_find_unique_id(items: list, master_list_db_path: str):
    table_name: str = 'master'
    con = sqlite3.connect(master_list_db_path)

    for i in items:
        item: InvoiceData = i
        if item.lci_id and item.portfolio_id:
            log(f'Already processed {item.case}')
            continue

        case_number: str = item.case.strip()
        if '-' in case_number:
            case_number = case_number.replace('-', '0')
        elif 'B' in case_number:
            case_number = case_number.replace('B', '0')
        else:
            case_number = case_number[0:2] + '0' + case_number[2:]

        scenarios: list = [
            # Scenario 1: If Case/Name/Last 4 digits of account match
            f'SELECT * FROM {table_name} where lower("petition_sequence_number") == "{case_number.strip().lower()}" '
            f'AND lower("primary_debtor_fullname") == "{item.full_name.strip().lower()}" '
            f'AND lower("last_4_digits_of_account") == "{item.last4digits.strip().lower()}"',

            # Scenario 2: If Case/Name/Trustee matches
            f'SELECT * FROM {table_name} where lower("petition_sequence_number") == "{case_number.strip().lower()}" '
            f'AND lower("primary_debtor_fullname") == "{item.full_name.strip().lower()}" '
            f'AND lower("trustee_last_name") == "{item.trustee_last_name.strip().lower()}"',

            # Scenario 3: If Case/Trustee/Last 4 digits of account matches
            f'SELECT * FROM {table_name} where lower("petition_sequence_number") == "{case_number.strip().lower()}" '
            f'AND lower("last_4_digits_of_account") == "{item.last4digits.strip().lower()}" '
            f'AND lower("trustee_last_name") == "{item.trustee_last_name.strip().lower()}"',

            # Scenario 4: If Case/First Name/Trustee matches
            f'SELECT * FROM {table_name} where lower("petition_sequence_number") == "{case_number.strip().lower()}" '
            f'AND lower("primary_debtor_first") == "{item.first_name.strip().lower()}" '
            f'AND lower("trustee_last_name") == "{item.trustee_last_name.strip().lower()}"',

            # Scenario 5: If Case/Last Name/Trustee matches
            f'SELECT * FROM {table_name} where lower("petition_sequence_number") == "{case_number.strip().lower()}" '
            f'AND lower("primary_debtor_last") == "{item.last_name.strip().lower()}" '
            f'AND lower("trustee_last_name") == "{item.trustee_last_name.strip().lower()}"',

            # Scenario 6: If Case/Secondary Debtor Last Name/Trustee matches
            # TODO Validate it
            f'SELECT * FROM {table_name} where lower("petition_sequence_number") == "{case_number.strip().lower()}" '
            f'AND lower("secondary_debtor_last") == "{item.secondary_debtor_last_name}" '
            f'AND lower("trustee_last_name") == "{item.trustee_last_name.strip().lower()}"',

            # Scenario 7: If Case/Claim/Trustee matches
            f'SELECT * FROM {table_name} where lower("petition_sequence_number") == "{case_number.strip().lower()}" '
            f'AND lower("claim_number") == "{item.claim.strip().lstrip("0").lower()}" '
            f'AND lower("trustee_last_name") == "{item.trustee_last_name.strip().lower()}"',

            # Scenario 8: If Case/Redacted Account number matches
            # TODO Validate it
            f'SELECT * FROM {table_name} where lower("petition_sequence_number") == "{case_number.strip().lower()}" '
            f'AND lower("account_number") == "{00000000000000000000000000000000}"',

            # Scenario 9: (edge case when trustees retire): If Case/State/Name matches
            f'SELECT * FROM {table_name} where lower("petition_sequence_number") == "{case_number.strip().lower()}" '
            f'AND lower("primary_debtor_fullname") == "{item.full_name.strip().lower()}" '
            f'AND lower("state") == "{item.trustee_state.strip().lower()}"',

            # Scenario 10: My custom case: If Case/Debtor first and last/Last 4 digits of account match
            f'SELECT * FROM {table_name} where lower("petition_sequence_number") == "{case_number.strip().lower()}" '
            f'AND lower("primary_debtor_first") == "{item.first_name.strip().lower()}" '
            f'AND lower("primary_debtor_last") == "{item.last_name.strip().lower()}" '
            f'AND lower("last_4_digits_of_account") == "{item.last4digits.strip().lower()}"',
        ]

        for scenario in scenarios:
            cur = con.execute(scenario)
            rows: list = cur.fetchall()
            log(f'Case: {item.case}. Scenario {scenarios.index(scenario) + 1}. Result {len(rows)}')
            if len(rows) == 0:
                continue
            item.lci_id = rows[0][0]
            item.portfolio_id = rows[0][1]
            item.true_owner = rows[0][2]
            item.servicing_fee = rows[0][3]
            if 'archive' in master_list_db_path.lower():
                item.putbacks = 'Y'
            if item.lci_id and not item.true_owner:
                item.true_owner = item.check_owner
            break

    con.close()
