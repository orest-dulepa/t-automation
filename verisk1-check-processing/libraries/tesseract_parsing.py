from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import os
import re



class PDF:
    def __init__(self, path_to_temp: str):
        self.path_to_temp: str = path_to_temp

    def get_page_as_images(self, path_to_pdf: str) -> list:
        pages_list: list = []

        pages: list = convert_from_path(path_to_pdf, 600)
        # i: int = 1
        for page in pages:
            # image_name: str = os.path.join(self.path_to_temp, f'Page_{i}.jpg')
            # page.save(image_name, "JPEG")
            # i = i + 1
            # pages_list.append(image_name)
            pages_list.append(page)
        return pages_list

    def parse(self, path_to_pdf: str, company_name: str):
        pages_list = self.get_page_as_images(path_to_pdf)

        invoice_data = {}
        for page in pages_list:
            page_text: str = pytesseract.image_to_string(page)

            lines: list = page_text.split('\n')
            position: int = 0
            while position < len(lines):
                line: str = lines[position]
                if not line:
                    position += 1
                    continue
                if 'CHAPTER 13 TRUSTEE' in line:
                    pass

                if 'Case#' in line:
                    position += 1
                    # skip empty rows
                    while not lines[position]:
                        position += 1
                    line = lines[position]
                    case: str = line.split()[0]
                    print(case)
                    name: str = ''

                    position += 1
                    line = lines[position]
                    if 'ACCT' in line:
                        account: str = re.findall(r'ACCT: (\d+)', line)[0]
                        print(account)

                position += 1

tesseract = {}
for file in tesseract:
    print(file)
    lines = tesseract[file].split('\n')

    position: int = 0
    while position < len(lines):
        line: str = lines[position]
        if not line:
            position += 1
            continue
        if 'CHAPTER 13'.lower() in line.lower() or 'TRUSTEE'.lower() in line.lower():
            print(lines[position - 2])
            print(lines[position - 1])
            print(lines[position])
            print(lines[position + 1])
            print(lines[position + 2])
            break
        position += 1
    print('=' * 10)
