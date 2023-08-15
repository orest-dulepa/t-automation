import os.path

from libraries.google_services.drive_service import GoogleDrive
from config import BOT_ACCOUNT, PROD, TEMP_FOLDER
import json

'''
from pdf2image import convert_from_path
import cv2
from PIL import Image

pdfs = r"C:\Users\Serhii\Desktop\0255101.pdf"
pages = convert_from_path(pdfs, 350)

i = 1
for page in pages:
    image_name = "Page_" + str(i) + ".jpg"
    page.save(image_name, "JPEG")
    i = i + 1


try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract

from pdf2image import convert_from_path

pdfs = r"tmp/0255101.pdf"
pages = convert_from_path(pdfs, 350)
pages_list = []
i = 1
for page in pages:
    image_name = "Page_" + str(i) + ".jpg"
    page.save(image_name, "JPEG")
    i = i+1
    pages_list.append(image_name)

'''



def main():
    drive: GoogleDrive = GoogleDrive(BOT_ACCOUNT)
    master_list: str = drive.download_file_by_name('Master List for Payments_20210610.xlsx', TEMP_FOLDER)
    master_archive: str = drive.download_file_by_name('Master List of Payments Archive_20210610.xlsx', TEMP_FOLDER)
    template: str = drive.download_file_by_name('Excel Payments Table_MMYYYY.xlsx', TEMP_FOLDER)

    client_name: str = '13/7, LLC'
    drive.download_pdf_from_folder(client_name, os.path.join(TEMP_FOLDER, client_name))


if __name__ == '__main__':
    main()
