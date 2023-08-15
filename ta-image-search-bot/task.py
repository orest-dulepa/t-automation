from libraries import common, google_search
import os
import platform
import psutil
import multiprocessing
import subprocess
import ta_bitwarden_cli
from RPA.Robocloud.Items import Items
import requests
import time


SETTINGS = {'url': 'https://images.google.com/?hl=en',
            'search_section': 'image',
            'search_term': ''}


def print_runtime_specs():
    print(platform.machine())
    print(platform.uname())
    print(platform.processor())
    print(str(round(psutil.virtual_memory().total / (1024.0 **3))) + " GB")
    print(str(multiprocessing.cpu_count())+" threads")
    print(str(psutil.cpu_count()) + " threads")
    a = os.statvfs('/')
    print(str(a.f_frsize * a.f_blocks) + " - total bytes")
    print(str((a.f_frsize * a.f_blocks) / (1024.0 ** 3)) + " - total GB")
    print(str(a.f_frsize * a.f_bavail) + " - free bytes")
    print(str((a.f_frsize * a.f_bavail) / (1024.0 ** 3)) + " - free GB")
    print(subprocess.run('lscpu', capture_output=True, text=True))
    print(subprocess.run(['free', '-h'], capture_output=True, text=True))


def main():
    # print_runtime_specs()
    common.log_message('Start Google Image Search Bot')
    common.log_message('Version 1.0.3')

    # For testing
    library = Items()
    library.load_work_item_from_environment()

    # Test
    items: dict = library.get_work_item_variables()
    print(items)

    search_term: str = str(library.get_work_item_variable('searchTerm')).strip()
    if 'error' in search_term.lower():
        print(f'Finishing the run with {search_term} status')
        exit(1)
    elif 'warning' in search_term.lower():
        print(f'Finishing the run with {search_term} status')
        response = requests.post(
            items['changeStatusUrl'],
            headers={'Authorization': f"Bearer {items['accessToken']}"},
            json={
                'runId': os.environ['RC_PROCESS_RUN_ID'],
                'newStatus': 'warning'
            }
        )
        print(response.status_code)
        time.sleep(5)
        exit(0)

    global SETTINGS
    SETTINGS = common.get_settings()

    common.log_message('20% task - Bot is setting up', 'INFO')
    gs = google_search.GoogleSearch(SETTINGS)
    if not gs.is_site_available:
        common.log_message('Google Search site is not available', 'ERROR')
        exit(1)

    common.log_message('50% task - Bot is searching for {}'.format(gs.search_term), 'INFO')
    gs.perform_search()
    if not gs.success:
        common.log_message('Google Search is unable to find {}'.format(gs.search_term), 'ERROR')
        exit(1)

    common.log_message('80% task - Image Search Bot is making screenshot' + 'of first result', 'INFO')
    gs.take_first_element_screenshot()
    if not gs.success:
        common.log_message('Image Search Bot is unable to take screenshot', 'ERROR')
        exit(1)

    common.log_message('100% task - Bot has completed its task', 'INFO')
    common.log_message('End Google Image Search Bot')


if __name__ == "__main__":
    main()
