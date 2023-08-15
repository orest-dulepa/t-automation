from loguru import logger
from RPA.Robocloud.Secrets import Secrets
import os
import platform
import subprocess
import zipfile
import json
import requests


class BitWarden:
    def __init__(self):
        self._get_bitwarden_credentials()

    def _get_bitwarden_credentials(self, credentials_name: str = 'bitwarden_credentials') -> dict:
        secrets = Secrets()
        bitwarden_credentials = secrets.get_secret(credentials_name)
        self.bw_credentials = bitwarden_credentials

    def _download_bitwarden(self, root_path: str) -> str:
        bitwarden_url = 'https://vault.bitwarden.com/download/?app=cli&platform='
        switcher = {'linux': 'linux', 'darwin': 'macos', 'windows': 'windows'}
        path_to_zip_file = os.path.join(root_path, 'temp', 'bitwarden.zip')
        path_to_exe_file = ''
        count = 0
        while count <= 3 and len(path_to_exe_file) == 0:
            try:
                count += 1
                if os.path.exists(path_to_zip_file):
                    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                        path_to_exe_file = os.path.join(root_path, 'temp', zip_ref.namelist()[0])
                else:
                    system_type = platform.system()
                    if switcher.get(system_type.lower()) != '':
                        logger.info('System type is {}'.format(system_type), 'TRACE')
                        r = requests.get(bitwarden_url + switcher.get(system_type.lower()), allow_redirects=True)
                        with open(path_to_zip_file, 'wb') as warden_zip:
                            warden_zip.write(r.content)
                        with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                            zip_ref.extract(zip_ref.namelist()[0], os.path.join(root_path, 'temp'))
                            path_to_exe_file = os.path.join(root_path, 'temp', zip_ref.namelist()[0])
                    else:
                        pass
                        logger.error("Can't identify the system: {}".format(system_type), 'ERROR')
            except:
                pass
                logger.error("Can't identify the system", 'ERROR')

        return path_to_exe_file

    def get_credentials(self, user_credentials_name: dict) -> dict:
        credentials = {}
        root_path = os.environ.get("ROBOT_ROOT", os.getcwd())

        logger.info('Getting credentials')
        if not os.path.exists(os.path.join(root_path, 'temp')):
            os.mkdir(os.path.join(root_path, 'temp'))
        path_to_exe_file = self._download_bitwarden(root_path)
        self.path_to_exe_file = path_to_exe_file
        if not os.path.exists(path_to_exe_file):
            return credentials
        if platform.system().lower() != 'windows':
            cmd = subprocess.run(['chmod', '+x', path_to_exe_file], capture_output=True, text=True)
        bitwarden_app = subprocess.run([path_to_exe_file, 'logout'], capture_output=True, text=True)

        retry_count = 0
        bitwarden_app = subprocess.run([path_to_exe_file, 'login', self.bw_credentials['username'], self.bw_credentials['password'], '--raw'], capture_output=True, text=True, timeout=180)
        while len(bitwarden_app.stdout) == 0 and retry_count < 5:
            bitwarden_app = subprocess.run(
                [path_to_exe_file, 'login', self.bw_credentials['username'], self.bw_credentials['password'], '--raw'], capture_output=True, text=True, timeout=180
            )
            retry_count += 1
        if len(bitwarden_app.stdout) > 0:
            bitwarden_token = bitwarden_app.stdout
            bitwarden_app = subprocess.run([path_to_exe_file, 'list', 'items', '--session', bitwarden_token], capture_output=True, text=True)
            bitwarden_items = json.loads(bitwarden_app.stdout)
            for credentials_key, credentials_name in user_credentials_name.items():
                for bw_item in bitwarden_items:
                    if credentials_name == bw_item['name']:
                        credentials[credentials_key] = {}
                        credentials[credentials_key]['login'] = bw_item['login']['username']
                        credentials[credentials_key]['password'] = bw_item['login']['password']
                        if 'uris' in bw_item['login']:
                            credentials[credentials_key]['url'] = bw_item['login']['uris'][0]['uri']
                        else:
                            credentials[credentials_key]['url'] = ''
                        if bw_item['login']['totp'] is None:
                            credentials[credentials_key]['otp'] = ''
                        else:
                            bitwarden_app = subprocess.run([path_to_exe_file, 'get', 'totp', bw_item['id'], '--session', bitwarden_token], capture_output=True, text=True)
                            credentials[credentials_key]['otp'] = bitwarden_app.stdout
                        if 'fields' in bw_item:
                            for field in bw_item['fields']:
                                credentials[credentials_key][field['name']] = field['value']
        else:
            logger.info("Can't get credentials from bitwarden. Please check it and re-run the bot. Potential reason: {}".format(bitwarden_app.stderr), 'ERROR')
            exit(1)
        if len(credentials) != len(user_credentials_name):
            logger.info("Can't get credentials from bitwarden. Please check it and re-run the bot", 'ERROR')
            exit(1)
        bitwarden_app = subprocess.run([path_to_exe_file, 'logout'], capture_output=True, text=True)
        return credentials

    def __del__(self):
        if hasattr(self, 'path_to_exe_file'):
            logger.info('bitwarden __del__ logout')
            try:
                subprocess.run([self.path_to_exe_file, 'logout'], capture_output=True, text=True)
            except (RuntimeError, LookupError) as e:
                logger.warning(e)
