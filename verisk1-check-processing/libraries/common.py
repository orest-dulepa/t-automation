import os
import boto3
import json
import requests


def log(message: object):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=os.environ.get('LOGS_QUEUE_NAME'))
    message_body = json.dumps({'processRunId': os.environ.get('PROCESS_RUN_ID'), 'message': str(message)})

    queue.send_message(MessageBody=message_body, MessageGroupId=os.environ.get('PROCESS_RUN_ID'))


def get_meta_item(meta, api_name: str):
    item = meta[
        [i for i in range(len(meta)) if meta[i]['api_name'] == api_name][0]
    ]

    return item['value']


def set_warning():
    res = requests.post(
        os.environ.get('CHANGE_STATUS_URL'),
        headers={'Authorization': f"Bearer {os.environ.get('ACCESS_TOKEN')}"},
        json={
            'runId': os.environ.get('PROCESS_RUN_ID'),
            'newStatus': 'warning'
        }
    )
    log(f'Set warning status_code: {res.status_code}')


def print_version():
    try:
        file = open('VERSION')
        try:
            log('Version {}'.format(file.read().strip()))
        except Exception as ex:
            log('Error reading VERSION file. {}'.format(str(ex)))
        finally:
            file.close()
    except Exception as e:
        log('VERSION file not found. {}'.format(str(e)))
