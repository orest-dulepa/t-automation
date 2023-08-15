import os
import io
import requests
import json

from pydrive.auth import GoogleAuth
from pydrive.drive import (
    GoogleDrive,
)
from libraries import common as com
from libraries.exceptions import EmptyGDrive


class GDrive:
    def __init__(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        self.drive = GoogleDrive(gauth)
        self.invoice_file_names = None

    def download_invoice_files(self, check_number):
        """
        Download all invoice files from GDrive to output/ dir
        """
        fileList = self.drive.ListFile(
            {"q": "title='{}'".format(check_number)}
        ).GetList()

        if not fileList:
            raise EmptyGDrive("Folder is empty or doesnt exist")

        com.log_message("Files in the folder '{}':".format(fileList[0]["title"]))

        fileList = self.drive.ListFile(
            {"q": "'{}' in parents and trashed=false".format(fileList[0]["id"])}
        ).GetList()

        self.invoice_file_names = [
            f
            for f in fileList
            if (
                (
                    "Invoice Details Behavioral Health Works" in f["title"]
                    or "BHPN" in f["title"]
                    or "BHW" in f["title"]
                )
                and ".xls" in f["title"]
            )
        ]
        for f in self.invoice_file_names:
            com.log_message("title: {}, id: {}".format(f["title"], f["id"]))
            f.GetContentFile(f["title"])
            os.rename(f["title"], "output/{}".format(f["title"]))
