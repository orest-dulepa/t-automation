import boto3
import sqlite3
import json
import pandas
from shutil import copyfile
from os.path import join, basename
from datetime import datetime, date, timedelta
from libraries.google_services.drive_service import GoogleDrive
from libraries.common import log
from config import BOT_ACCOUNT, PROD, TEMP_FOLDER
from openpyxl import load_workbook
from libraries.report import Report


def lambda_handler(event, context):
    bucket_name: str = 'verisk1-dev'

    log('=== start ===')
    log('event')
    log(event)

    # Get input variables
    template_file_name: str = event['template_name']

    # Get files from S3
    s3 = boto3.client('s3')
    template_file_path: str = join(TEMP_FOLDER, template_file_name)
    s3.download_file(bucket_name, template_file_name, template_file_path)

    current_report_name: str = template_file_name.replace('MMYYYY', date.today().strftime('%m%Y'))
    drive: GoogleDrive = GoogleDrive(BOT_ACCOUNT)
    items: list = drive.get_items_in_folder('Verisk LCI - Check Processing')
    current_report_id: str = drive.get_file_id(current_report_name, items)

    current_report_path: str = ''
    if current_report_id:
        current_report_path = drive.download_file_by_name(current_report_name, TEMP_FOLDER, current_report_id)
    else:
        current_report_path = join(TEMP_FOLDER, current_report_name)
        copyfile(join(TEMP_FOLDER, template_file_name), current_report_path)

    parsed_data = get_data_from_parsed_files(bucket_name)
    write_data_to_report(current_report_path, parsed_data)

    s3.upload_file(current_report_path, bucket_name, 'result_' + basename(current_report_path))
    if current_report_id:
        drive.update_file(current_report_path, current_report_id)
    else:
        root_folder_id: str = drive.get_item_id('Verisk LCI - Check Processing')
        drive.upload_file(current_report_path, root_folder_id)

    if date.today().day == 15:
        report: Report = Report(drive, template_file_name, template_file_path, parsed_data, current_report_path)
        report.prepare_data(items)
        report.write_and_upload_data()

    return {
        'statusCode': 200,
        'body': json.dumps('The End')
    }


def write_data_to_report(current_report_path: str, parsed_data: list):
    df_template = pandas.read_excel(current_report_path)

    book = load_workbook(current_report_path)
    writer = pandas.ExcelWriter(current_report_path, engine='openpyxl')
    writer.book = book
    writer.sheets = {ws.title: ws for ws in book.worksheets}
    pandas.DataFrame(parsed_data).to_excel(writer, startrow=len(df_template.index) + 1, index=False, header=False)
    writer.save()


def get_data_from_parsed_files(bucket_name: str) -> list:
    s3 = boto3.client('s3')
    objects = s3.list_objects(Bucket=bucket_name)

    parsed_files: list = []
    for obj in objects['Contents']:
        if not obj['Key'].endswith('_parsed.json'):
            continue
        temp_path: str = join(TEMP_FOLDER, obj['Key'])
        s3.download_file(bucket_name, obj['Key'], temp_path)
        parsed_files.append(temp_path)
        s3.delete_object(Bucket=bucket_name, Key=obj['Key'])

    parsed_data: list = []
    for file in parsed_files:
        try:
            with open(file) as f:
                parsed_data += json.load(f)
        except Exception as ex:
            log(str(ex))
            log(file)

    return parsed_data
