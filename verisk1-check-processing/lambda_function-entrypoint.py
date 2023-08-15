import boto3
import sqlite3
import json
import pandas
import time
import os
from os.path import basename
from datetime import date, datetime
from libraries.google_services.drive_service import GoogleDrive
from libraries.common import log, get_meta_item, set_warning
from config import BOT_ACCOUNT, PROD, TEMP_FOLDER
import asyncio


async def start_pdf_parsing(client, function_pdf_parsing: str, payload):
    response = client.invoke(
        FunctionName=function_pdf_parsing,
        InvocationType='RequestResponse',
        Payload=payload
    )
    # Event
    print(response)


def lambda_handler(event, context):
    os.environ['PROCESS_RUN_ID'] = event.get('processRunId')
    os.environ['CHANGE_STATUS_URL'] = event.get('changeStatusUrl')
    os.environ['ACCESS_TOKEN'] = event.get('accessToken')

    phrase = get_meta_item(event.get('meta'), 'phrase')

    bucket_name: str = 'verisk1-dev'
    function_pdf_parsing: str = 'verisk1-dev-pdf-parsing'

    log('=== start ===')
    log('Phrase:')
    log(phrase)
    log('Event:')
    log(event)

    # Download files from GD
    drive: GoogleDrive = GoogleDrive(BOT_ACCOUNT)

    master_list: str = drive.download_file_by_name('Master List for Payments.xlsx', TEMP_FOLDER)
    master_archive: str = drive.download_file_by_name('Master List of Payments Archive.xlsx', TEMP_FOLDER)
    template: str = drive.download_file_by_name('Excel Payments Table_MMYYYY.xlsx', TEMP_FOLDER)

    # TEST
    master_list_db_path = master_list.lower().replace('.xlsx', '.db')
    master_archive_db_path = master_archive.lower().replace('.xlsx', '.db')
    '''
    # Convert Excel to sqlite3
    master_list_db_path: str = convert_master_file_to_db(master_list)
    master_archive_db_path: str = convert_master_file_to_db(master_archive)

    # Upload files to S3
    s3 = boto3.client('s3')
    s3.upload_file(master_list_db_path, bucket_name, basename(master_list_db_path))
    s3.upload_file(master_archive_db_path, bucket_name, basename(master_archive_db_path))
    s3.upload_file(template, bucket_name, basename(template))
    '''
    # Trigger PDF-parsing lambda for each file
    client = boto3.client('lambda')
    folders: list = drive.get_items_in_folder('checks')

    entered_folder_name: str = f'{date.today().strftime("%m%d%Y")} Entered'
    manual_folder: str = 'For manual processing'
    log(entered_folder_name)

    processed_files: int = 0
    for folder in folders:
        if 'folder' not in folder['mimeType']:
            continue
        files: list = drive.get_items_in_folder(folder['name'], folder['id'])

        entered_folder_id: str = ''
        manual_folder_id: str = ''
        for file in files:
            if not file['name'].lower().endswith('.pdf'):
                continue
            print(folder['name'], folder['id'], file['name'], file['id'])
            processed_files += 1

            if not entered_folder_id:
                entered_folder_id = drive.get_or_create_folder(entered_folder_name, files, folder['id'], True)
                manual_folder_id = drive.get_or_create_folder(manual_folder, files, folder['id'], True)

            '''
            print(datetime.now())
            payload = bytes(json.dumps({
                    'file_name': file['name'],
                    'file_id': file['id'],
                    'parent_folder_id': folder['id'],
                    'template_name': basename(template),
                    'master_list_db': basename(master_list_db_path),
                    'master_list_archive_db': basename(master_archive_db_path),
                    'entered_folder_id': entered_folder_id,
                    'manual_folder_id': manual_folder_id
                }).encode('UTF-8'))

            task = loop.create_task(start_pdf_parsing(client, function_pdf_parsing, payload))
            future_dds_responses.append(start_pdf_parsing(client, function_pdf_parsing, payload))

            if processed_files >= 5:
                return json.dumps({"status": "end Test", "template_name": basename(template)})
            '''
            response = client.invoke(
                FunctionName=function_pdf_parsing,
                InvocationType='Event',
                Payload=bytes(json.dumps({
                    'file_name': file['name'],
                    'file_id': file['id'],
                    'parent_folder_id': folder['id'],
                    'template_name': basename(template),
                    'master_list_db': basename(master_list_db_path),
                    'master_list_archive_db': basename(master_archive_db_path),
                    'entered_folder_id': entered_folder_id,
                    'manual_folder_id': manual_folder_id
                }).encode('UTF-8'))
            )
            time.sleep(1)

        time.sleep(1)
    log(f'Processed {processed_files} files')

    if 'error' in phrase.lower():
        raise Exception('Custom exception')
    elif 'warning' in phrase.lower():
        set_warning()
        exit(0)

    # if processed_files > 0:
    #    time.sleep(60 * 3)

    return json.dumps({"status": "end", "template_name": basename(template)})


def convert_master_file_to_db(master_list_excel: str) -> str:
    pd = pandas.read_excel(master_list_excel)
    columns: list = []
    for column in pd.columns:
        columns.append(column.strip().lower().replace(' ', '_'))
    pd.columns = columns

    master_list_db_path: str = master_list_excel.lower().replace('.xlsx', '.db')
    con = sqlite3.connect(master_list_db_path)
    pd.to_sql('master', con, index=False, if_exists="replace")
    con.commit()
    con.close()

    return master_list_db_path
