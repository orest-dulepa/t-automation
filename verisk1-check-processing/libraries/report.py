import boto3
import sqlite3
import json
import pandas
from shutil import copyfile
from os.path import join, basename
from datetime import datetime, date, timedelta
from libraries.google_services.drive_service import GoogleDrive
from config import BOT_ACCOUNT, PROD, TEMP_FOLDER
from openpyxl import load_workbook


class Report:
    def __init__(self, drive: GoogleDrive, template_file_name: str, template_file_path: str, current_run_items: list, current_report_path: str):
        self.drive: GoogleDrive = drive
        self.template_file_name: str = template_file_name
        self.template_file_path: str = template_file_path
        self.current_run_items: list = current_run_items
        self.current_run = pandas.DataFrame(self.current_run_items)
        self.current_report_path: str = current_report_path
        self.results: dict = {}

    def write_and_upload_data(self):
        month_end_folder: str = 'Month-End Reports'
        month_end_files: list = self.drive.get_items_in_folder(month_end_folder)

        file_pattern: str = '{0} {1}'
        previous_month = date.today().replace(day=1) - timedelta(days=1)
        previous_month_str: str = previous_month.strftime('%b %Y')

        index: int = 0
        for client in self.results:
            file_name: str = file_pattern.format(client, previous_month_str)
            file_id: str = self.drive.get_file_id(file_name, month_end_files)

            report_path: str = ''
            if file_id:
                report_path = self.drive.download_file_by_name(file_name, TEMP_FOLDER, file_id)
                # self.drive.update_file(current_report_path, current_report_id)
            else:
                report_path = join(TEMP_FOLDER, f'report{index}.xlsx')
                copyfile(self.template_file_path, report_path)

                book = load_workbook(report_path)
                writer = pandas.ExcelWriter(report_path, engine='openpyxl')
                writer.book = book
                writer.sheets = {ws.title: ws for ws in book.worksheets}
                self.results[client].to_excel(writer, startrow=2, index=False, header=False)
                writer.save()

                root_folder_id: str = self.drive.get_item_id(month_end_folder)
                self.drive.upload_file(report_path, root_folder_id, file_name)
                print(f'File {file_name} uploaded to GD')

    @staticmethod
    def remove_not_valid_rows(table):
        start_date: date = date.today()
        previous_month = date.today().replace(day=1) - timedelta(days=1)
        end_date: date = previous_month.replace(day=16)

        for index, row in table.iterrows():
            date_str: str = row['entered date']
            try:
                date_obj: date = datetime.strptime(date_str, '%m/%d/%Y').date()
                if start_date >= date_obj >= end_date:
                    pass
                else:
                    table = table.drop(index)
            except Exception as ex:
                print(str(ex))
                table = table.drop(index)
        return table

    def prepare_data(self, items: list):
        previous_month = date.today().replace(day=1) - timedelta(days=1)
        previous_report_name: str = self.template_file_name.replace('MMYYYY', previous_month.strftime('%m%Y'))
        previous_report_id: str = self.drive.get_file_id(previous_report_name, items)
        if previous_report_id:
            previous_report_path = self.drive.download_file_by_name(previous_report_name, TEMP_FOLDER, previous_report_id)
            previous_report = pandas.read_excel(previous_report_path)
            previous_report = self.remove_not_valid_rows(previous_report)
        else:
            previous_report = pandas.DataFrame()

        current_report = pandas.read_excel(self.current_report_path)
        merged_reports = pandas.concat([current_report, previous_report])
        columns: list = []
        for column in merged_reports.columns:
            columns.append(column.strip().lower())
        merged_reports.columns = columns

        self.prepare_month_reports(merged_reports)

    def get_client_folders(self):
        client_folders: list = []
        folders: list = self.drive.get_items_in_folder('checks')

        for folder in folders:
            if 'folder' not in folder['mimeType']:
                continue
            client_folders.append(folder['name'])
        return client_folders

    def prepare_month_reports(self, merged_reports):
        client_folders: list = self.get_client_folders()

        self.results = {}
        for index, row in merged_reports.iterrows():
            for client in client_folders:
                temp_clint: str = client.lower().replace(', llc', '').replace(', inc', '')
                if temp_clint in str(row['true owner']).lower() or temp_clint in str(row['check owner']).lower():
                    if client not in self.results:
                        self.results[client] = pandas.DataFrame(data=None, columns=merged_reports.columns)
                    self.results[client] = self.results[client].append(row)
                    break
