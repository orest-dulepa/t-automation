import os
import re
from PIL import Image
import pytesseract
from pdf2image import convert_from_path


class OcrPdf:
    def __init__(self, path_to_pdf):
        self.path = path_to_pdf
        self.pages_text = []

    def prepare_amount_of_pages(self, amount_of_pages: int = 1):
        pages = convert_from_path(self.path, 300, last_page=amount_of_pages)
        image_counter = 1
        for page in pages:
            filename = "page_" + str(image_counter) + ".jpg"
            page.save(filename, 'JPEG')
            image_counter = image_counter + 1
            if image_counter > amount_of_pages:
                break

        filelimit = image_counter - 1
        for i in range(1, filelimit + 1):
            filename = "page_" + str(i) + ".jpg"
            text = str((pytesseract.image_to_string(Image.open(filename), config='--psm 4')))
            text = text.replace('-\n', '')
            self.pages_text.append(text)
            os.remove(filename)

    def prepare_special_page(self):
        pages = convert_from_path(self.path, 500, last_page=4)
        image_counter = 1
        for page in pages:
            filename = "page_" + str(image_counter) + ".jpg"
            page.save(filename, 'JPEG')
            image_counter = image_counter + 1
            if image_counter > 4:
                break

        filelimit = image_counter - 1
        for i in range(1, filelimit + 1):
            filename = "page_" + str(i) + ".jpg"
            if i == 4:
                colorImage = Image.open(filename)
                if colorImage.width < colorImage.height:
                    transposed = colorImage.transpose(Image.ROTATE_270)
                    transposed.save(filename)
                    try:
                        transposed.close()
                    except:
                        pass
                try:
                    colorImage.close()
                except:
                    pass
            text = str((pytesseract.image_to_string(Image.open(filename))))
            text = text.replace('-\n', '')
            self.pages_text.append(text)
            os.remove(filename)

    def prepare_pdf(self):
        """
        Part #1 : Converting PDF to images
        Spliting pdf file to page images to process them via Tesseract
        Declaring filename for each page of PDF as JPG
            For each page, filename will be:
            PDF page 1 -> page_1.jpg
            PDF page 2 -> page_2.jpg
            PDF page 3 -> page_3.jpg
            ....
            PDF page n -> page_n.jpg

        Part #2 - Recognizing text from the images using OCR
        The recognized text is stored in variable text
            Any string processing may be applied on text
            Here, basic formatting has been done:
            In many PDFs, at line ending, if a word can't
            be written fully, a 'hyphen' is added.
            The rest of the word is written in the next line
            Eg: This is a sample text this word here GeeksF-
            orGeeks is half on first line, remaining on next.
            To remove this, we replace every '-\n' to ''.
        """
        pages = convert_from_path(self.path, 500)
        image_counter = 1
        for page in pages:
            filename = "page_" + str(image_counter) + ".jpg"
            page.save(filename, 'JPEG')
            image_counter = image_counter + 1

        filelimit = image_counter - 1
        for i in range(1, filelimit + 1):
            filename = "page_" + str(i) + ".jpg"
            text = str((pytesseract.image_to_string(Image.open(filename), config='--psm 4')))
            text = text.replace('-\n', '')
            self.pages_text.append(text)
            os.remove(filename)

    def find_text_by_re(self, pattern: str, page: int = -1):
        """
        pattern - pattern to search specific text in pdf
        page - specify page number to search. -1 default and indicates search all pages
        """
        matches = []
        if page == -1:
            for pg in self.pages_text:
                temp = re.findall(pattern, pg)
                for t in temp:
                    matches.append(t)
        else:
            temp = re.findall(pattern, self.pages_text[page - 1])
            for t in temp:
                matches.append(t)
        return matches

# get filled date regex:
# b=a.find_text_by_re(r'(?:Filed.\s)(.*)(?:\s.+)')
