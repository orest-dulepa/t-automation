from libraries import common as com
import os
import zipfile
import requests
import subprocess
import platform


class Qpdf:
    def __init__(self):
        self.root_path = os.environ.get("ROBOT_ROOT", os.getcwd())
        self.path_to_zip_file = os.path.join(self.root_path, 'temp', 'qpdf.zip')
        self.path_to_exe_file = self.download(self.root_path)
        print('')

    def decode_pdf(self, src_pdf, dst_pdf):
        subprocess.run([self.path_to_exe_file, '--qdf', '--object-streams=disable', src_pdf, dst_pdf], text=True)

    def download(self, root_path: str) -> str:
        qpdf_url = 'https://downloads.sourceforge.net/project/qpdf/qpdf/10.1.0/qpdf-10.1.0-bin-linux-x86_64.zip'

        system_type = platform.system()
        if system_type == "Windows":
            path_to_exe_file = 'qpdf'
            return path_to_exe_file
        else:
            path_to_exe_file = ''
            count = 0
            while count <= 3 and len(path_to_exe_file) == 0:
                try:
                    count += 1
                    if os.path.exists(self.path_to_zip_file):
                        with zipfile.ZipFile(self.path_to_zip_file, 'r') as zip_ref:
                            path_to_exe_file = os.path.join(root_path, 'temp', 'bin', 'qpdf')
                    else:
                        r = requests.get(qpdf_url, allow_redirects=True)
                        open(self.path_to_zip_file, 'wb').write(r.content)
                        with zipfile.ZipFile(self.path_to_zip_file, 'r') as zip_ref:
                            zip_ref.extract(zip_ref.namelist()[0], os.path.join(root_path, 'temp'))
                            path_to_exe_file = os.path.join(root_path, 'temp', 'bin', 'qpdf')
                except Exception as ex:
                    com.log_message("Unexpected error: " + ex, 'ERROR')
            return path_to_exe_file
