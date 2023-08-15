import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class Table:
    def __init__(self, header_values: list, is_numerate=False):
        self.header_values = header_values
        self.title = ''
        self.is_numerate = is_numerate
        if self.is_numerate:
            self.header_html = ''.join([th(v) for v in ['№'] + header_values])
        else:
            self.header_html = ''.join([th(v) for v in header_values])

        self.rows = []
        self.in_html = ''

    def add_row(self, row_values: list):
        if len(row_values) != len(self.header_values):
            raise Exception("Count of row values should be as count of header values")

        for idx, value in enumerate(row_values):
            if type(value) is bool:
                row_values[idx] = to_check_mark(value)

        if self.is_numerate:
            row_number = len(self.rows) + 1
            row = tr(''.join([td_small(row_number)] + [td(v) for v in row_values]))
        else:
            row = tr(''.join([td(v) for v in row_values]))

        self.rows.append(row)

    def add_title(self, title: str):
        self.title = f"<p class='table-title'>{title}</p>"

    def get_html(self):
        return self.title + f'<table><thead>{self.header_html}</thead><tbody>{"".join(self.rows)}</tbody></table>'


class ReportConstructor:
    def __init__(self):
        with open(os.path.join(CURRENT_DIR, 'report_style.css'), 'r') as f:
            self.style = f.read()
        self.body = ''
        self.attachments = [os.path.join(CURRENT_DIR, 'images/otto.png')]

    def add_text(self, text: str):
        self.body += text.replace('\n', '<br>')

    def add_warning_message(self, message: str):
        message = message.replace("\n", "<br>")
        self.body += f'<br><div class="warning">{message}</div><br>'

    def add_footer(self, text: str):
        self.body += img_ta()
        self.add_text(text)
        self.attachments.append(os.path.join(CURRENT_DIR, 'images/ta.jpg'))

    def add_image(self, file_path, width=100):
        self.body += f'<img src="cid:{os.path.basename(file_path)}" ' \
                     f'alt="" style="display:block; margin:5px auto; width:{width}px">'
        self.attachments.append(os.path.abspath(file_path))

    def add_table(self, table: Table):
        self.body += table.get_html()

    def get_html(self):
        return f'<head><style>{self.style}</style></head>{body(self.body)}'


def body(s):
    return f'<body style="background:#a0a0a0;font-weight: 400;color:rgb(33, 37, 41);font-family:Roboto,sans-serif;line-height:1.6;font-size:15px;padding:10px 20px 30px">' \
           f'<div style="height:110px;margin:0px auto 4px;">' \
           f'<img src="cid:otto.png" alt="" style="display:block;margin:auto;width:110px">' \
           f'</div>' \
           f'<div class="wrpper">{s}</div>' \
           f'</body>'


def to_check_mark(status: bool):
    return '✔️' if status else '❌'


def td(s):
    return f'<td>{s}</td>'


def td_small(s):
    return f'<td class="small">{s}</td>'


def tr(s):
    return f'<tr>{s}</tr>'


def th(s):
    return f'<th>{s}</th>'


def img_ta():
    return '<img src="cid:ta.jpg" alt="" style="float:right; width:50px">'
