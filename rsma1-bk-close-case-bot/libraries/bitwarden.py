from libraries import common as com
from os import path
import os
import platform
import subprocess
import zipfile
import json
import requests

class Bitwarden:
    def __init__(self, credentials: dict):
        self.credentials = {}
        self.bitwarden_credentials = credentials
        self.root_path = os.environ.get("ROBOT_ROOT", os.getcwd())
        if not path.exists(os.path.join(self.root_path, 'temp')):
            os.mkdir(os.path.join(self.root_path, 'temp'))
        self.path_to_zip_file = os.path.join(self.root_path, 'temp', 'bitwarden.zip')
        self.path_to_exe_file = self.download_bitwarden(self.root_path)
        if platform.system().lower() != 'windows':
            cmd = subprocess.run(['chmod', '+x', self.path_to_exe_file], capture_output=True, text=True)
        if platform.system().lower() == 'darwin':
            bitwarden_app = subprocess.run(['sudo', self.path_to_exe_file, 'logout'], capture_output=True, text=True)
        else:
            bitwarden_app = subprocess.run([self.path_to_exe_file, 'logout'], capture_output=True, text=True)

    def download_bitwarden(self, root_path: str) -> str:
        bitwarden_url = 'https://vault.bitwarden.com/download/?app=cli&platform='
        switcher = {'linux': 'linux', 'darwin': 'macos', 'windows': 'windows'}

        path_to_exe_file = ''
        count = 0
        while count <= 3 and len(path_to_exe_file) == 0:
            try:
                count += 1
                if os.path.exists(self.path_to_zip_file):
                    with zipfile.ZipFile(self.path_to_zip_file, 'r') as zip_ref:
                        path_to_exe_file = os.path.join(root_path, 'temp', zip_ref.namelist()[0])
                else:
                    system_type = platform.system()
                    if switcher.get(system_type.lower()) != '':
                        com.log_message('System type is {}'.format(system_type), 'TRACE')
                        r = requests.get(bitwarden_url + switcher.get(system_type.lower()), allow_redirects=True)
                        open(self.path_to_zip_file, 'wb').write(r.content)
                        with zipfile.ZipFile(self.path_to_zip_file, 'r') as zip_ref:
                            zip_ref.extract(zip_ref.namelist()[0], os.path.join(root_path, 'temp'))
                            path_to_exe_file = os.path.join(root_path, 'temp', zip_ref.namelist()[0])
                    else:
                        com.log_message("Can't identify the system: {}".format(system_type), 'ERROR')
            except Exception as ex:
                print(ex)
                com.log_message("Can't identify the system", 'ERROR')

        return path_to_exe_file

    def get_credentials(self, user_credentials_name: dict) -> dict:
        self.credentials = {}

        com.log_message('Getting credentials')
        if not os.path.exists(self.path_to_exe_file):
            return self.credentials

        retry_count = 0
        if platform.system().lower() == 'darwin':
            bitwarden_app = subprocess.run(['sudo', self.path_to_exe_file, 'login', self.bitwarden_credentials['username'], self.bitwarden_credentials['password'], '--raw'], capture_output=True, text=True, timeout=180)
        else:
            bitwarden_app = subprocess.run([self.path_to_exe_file, 'login', self.bitwarden_credentials['username'], self.bitwarden_credentials['password'], '--raw'], capture_output=True, text=True, timeout=180)
        while len(bitwarden_app.stdout) == 0 and retry_count < 5:
            if platform.system().lower() == 'darwin':
                bitwarden_app = subprocess.run(['sudo', self.path_to_exe_file, 'login', self.bitwarden_credentials['username'], self.bitwarden_credentials['password'], '--raw'], capture_output=True, text=True, timeout=180)
            else:
                bitwarden_app = subprocess.run([self.path_to_exe_file, 'login', self.bitwarden_credentials['username'], self.bitwarden_credentials['password'], '--raw'], capture_output=True, text=True, timeout=180)
            retry_count += 1
        if len(bitwarden_app.stdout) > 0:
            bitwarden_token = bitwarden_app.stdout
            if platform.system().lower() == 'darwin':
                bitwarden_app = subprocess.run(['sudo', self.path_to_exe_file, 'list', 'items', '--session', bitwarden_token], capture_output=True, text=True)
            else:
                bitwarden_app = subprocess.run([self.path_to_exe_file, 'list', 'items', '--session', bitwarden_token], capture_output=True, text=True)
            bitwarden_items = json.loads(bitwarden_app.stdout)
            for credentials_key, credentials_name in user_credentials_name.items():
                for bw_item in bitwarden_items:
                    if credentials_name == bw_item['name']:
                        self.credentials[credentials_key] = {}
                        self.credentials[credentials_key]['login'] = bw_item['login']['username']
                        self.credentials[credentials_key]['password'] = bw_item['login']['password']
                        if 'uris' in bw_item['login']:
                            self.credentials[credentials_key]['url'] = bw_item['login']['uris'][0]['uri']
                        else:
                            self.credentials[credentials_key]['url'] = ''
                        if bw_item['login']['totp'] is None:
                            self.credentials[credentials_key]['otp'] = ''
                        else:
                            if platform.system().lower() == 'darwin':
                                bitwarden_app = subprocess.run(['sudo', self.path_to_exe_file, 'get', 'totp', bw_item['id'], '--session', bitwarden_token], capture_output=True, text=True)
                            else:
                                bitwarden_app = subprocess.run([self.path_to_exe_file, 'get', 'totp', bw_item['id'], '--session', bitwarden_token], capture_output=True, text=True)
                            self.credentials[credentials_key]['otp'] = bitwarden_app.stdout
                        if 'fields' in bw_item:
                            for field in bw_item['fields']:
                                self.credentials[credentials_key][field['name']] = field['value']
        else:
            com.log_message("Can't get credentials from bitwarden. Please check it and re-run the bot. Potential reason: {}".format(bitwarden_app.stderr), 'ERROR')
            exit(1)
        if len(self.credentials) != len(user_credentials_name):
            com.log_message("Can't get credentials from bitwarden. Please check it and re-run the bot", 'ERROR')
            exit(1)
        if platform.system().lower() == 'darwin':
            bitwarden_app = subprocess.run(['sudo', self.path_to_exe_file, 'logout'], capture_output=True, text=True)
        else:
            bitwarden_app = subprocess.run([self.path_to_exe_file, 'logout'], capture_output=True, text=True)
        return self.credentials
