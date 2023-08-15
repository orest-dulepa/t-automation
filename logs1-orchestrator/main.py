import sys, os
from pprint import pprint, pformat

import requests
from threading import Thread
from loguru import logger
from time import sleep
import json

from bitwarden import BitWarden

if not os.path.isdir('output'):
    os.mkdir('output')

os.environ["RPA_SECRET_MANAGER"] = "RPA.Robocloud.Secrets.FileSecrets"
os.environ["RPA_SECRET_FILE"] = os.path.join(os.getcwd(), 'secrets.json')
bit_warden = BitWarden()
creds = bit_warden.get_credentials({
    'bknce_s1': 'LOGS1 Stage 1',
})


def get_artifacts(workspace_id, process_id, process_run_id, robot_run_id, headers, output_dir):
    url = f"https://api.eu1.robocorp.com/process-v1/" \
          f"workspaces/{workspace_id}/processes/{process_id}/" \
          f"runs/{process_run_id}/robotRuns/{robot_run_id}/artifacts"
    r = requests.get(
        url=url, headers=headers
    )
    if r.status_code != 200:
        raise ConnectionError(f'unable to download artifacts for {robot_run_id} - {r}')
    # logger.info(f"{r} - {r.content.title()} - {pformat(r.text)}")
    # logger.info(pformat(r.json()))
    for file in r.json():
        if file['fileName'].endswith('.log'):
            artifct_url = f"https://api.eu1.robocorp.com/" \
                          f"workspaces/{workspace_id}/" \
                          f"processes/{process_id}/" \
                          f"runs/{process_run_id}/" \
                          f"robotRuns/{robot_run_id}/" \
                          f"artifacts/{file['id']}/{file['fileName']}"
            logger.warning(artifct_url)
            file_r = requests.get(
                url=artifct_url, headers=headers
            )
            logger.info(r)
            logger.info(f'\n{pformat(file_r.json(),)}')


def get_robot_run(workspace_id, process_id, process_run_id, robot_run_id, headers):
    status_url = f'https://api.eu1.robocorp.com/process-v1/' \
                 f'workspaces/{workspace_id}/processes/{process_id}/' \
                 f'runs/{process_run_id}/robotRuns/{robot_run_id}/events'
    r = requests.get(url=status_url, headers=headers)
    pprint(r.json())


def bknce_stage_1():
    logger.info('launching BKNCE Stage 1')

    in_production = os.environ.get("BKNCE_PROD") == 'true'
    if in_production:
        logger.info('Configuring for PROD')
        output_dir = r'\\logs.com\dc\BKFiles\BK-NCEDocs\Working'
        auth_header = creds['bknce_s1']['PROD_Authorization']
        workspace_id = creds['bknce_s1']['PROD_WorkspaceId']
        process_id = creds['bknce_s1']['PROD_ProcessId']
        test_limit = None
        work_items = [
            {
                "offices": ["VA", "NY"]
            },
            {
                "offices": ["TN", "OK", "KS"]
            },
            {
                "offices": ["NC", "MO"]
            },
            {
                "offices": ["MS", "MN"]
            },
            {
                "offices": ["GA", "LA"]
            },
            {
                "offices": ["OIK", "FL"]
            },
            {
                "offices": ["TX", "ILD"]
            },
            {
                "offices": ["PA", "NJC"]
            }
        ]
    else:
        logger.info('Configuring for DEV')
        output_dir = r'\\logs.com\UAT\UATBKFiles\TestFolder1'
        auth_header = creds['bknce_s1']['DEV_Authorization']
        workspace_id = creds['bknce_s1']['DEV_WorkspaceId']
        process_id = creds['bknce_s1']['DEV_ProcessId']
        test_limit = 1
        work_items = [
            {
                "offices": [
                    "VA",
                    # "NY"
                ]
            },
            # {
            #     "offices": ["TN", "OK", "KS"]
            # },
            {
                "offices": [
                    "NC",
                    # "MO"
                ]
            },
            # {
            #     "offices": ["MS", "MN"]
            # },
            # {
            #     "offices": ["GA", "LA"]
            # },
            # {
            #     "offices": ["OIK", "FL"]
            # },
            # {
            #     "offices": ["TX", "ILD"]
            # },
            # {
            #     "offices": ["PA", "NJC"]
            # }
        ]

    headers = {
        'Authorization': auth_header
    }
    # Defined here and not in a JSON to avoid robocloud caching issues
    for w in work_items:
        w.update(dict(
            output_dir=output_dir,
            test_limit=test_limit
        ))

    response = requests.post(
        url=f'https://api.eu1.robocorp.com/process-v1/'
            f'workspaces/{workspace_id}/'
            f'processes/{process_id}/runs-batch',
        headers=headers,
        data=json.dumps(work_items)
    )
    if response.status_code != 200:
        raise RuntimeError(f'API call returned {response.status_code} - {response.text}')
    response_data = json.loads(response.text)
    logger.info(f'{response}\n{pformat(response_data)}')
    logger.info(f'Launched workitems successfully')

    def check_for_logs(run_id):
        logger.info('Waiting for log files ...')
        complete_ratio = None
        robot_runs = None
        while True:
            sleep(10)
            r = requests.get(
                url='https://api.eu1.robocorp.com/process-v1/'
                    f'workspaces/{workspace_id}/'
                    f'processes/{process_id}/'
                    f'runs/{run_id}',
                headers=headers
            )
            polling_response_data = json.loads(r.text)
            stats = polling_response_data['workItemStats']
            new_complete_ratio = (stats['failedCount'] + stats['succeededCount'])/stats['totalCount']
            if robot_runs is None and polling_response_data.get('robotRuns'):
                robot_runs = [run['id'] for run in polling_response_data['robotRuns']]
                logger.info(f'setting robot_runs: {robot_runs}')
            if new_complete_ratio != complete_ratio:
                logger.info(f'{int(new_complete_ratio * 100)}% complete')
                complete_ratio = new_complete_ratio
            if complete_ratio == 1:
                break
        logger.info('Run is complete')

        if robot_runs is not None:
            for robot_run in robot_runs:
                get_artifacts(workspace_id, process_id, run_id, robot_run, headers, output_dir='output')
                # get_robot_run(workspace_id, process_id, run_id, headers)
                get_robot_run(workspace_id, process_id, run_id, robot_run, headers)

    Thread(
        target=check_for_logs, args=(response_data['id'], )
    ).start()


def main(*launching):
    launching = launching or sys.argv[1:]
    for func_to_run in launching:
        globals()[func_to_run]()


if __name__ == '__main__':
    main('bknce_stage_1')
