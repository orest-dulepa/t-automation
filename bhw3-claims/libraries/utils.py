import inspect

from retry import retry


class BadRequestException(Exception):
    pass

class ScheduledMaintenanceException(Exception):
    pass

def retry_if_bad_request(func):
    attempt = 1

    @retry(exceptions=BadRequestException, tries=3, delay=1, backoff=2)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BadRequestException as ex:
            nonlocal attempt
            print('Bad request', f'Attempt {attempt}', str(ex))
            attempt += 1
            raise ex
    return wrapper

