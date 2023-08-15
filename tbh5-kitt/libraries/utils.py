from retry import retry

from libraries.common import log_message


class BadRequestException(Exception):
    pass


class ScheduledMaintenanceException(Exception):
    pass


def retry_if_bad_request(func):
    attempt = 1
    tries = 3

    @retry(exceptions=BadRequestException, tries=tries, delay=1, backoff=2)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BadRequestException as ex:
            nonlocal attempt
            log_message(f'Bad request Attempt {attempt}. {str(ex)}', 'WARN')
            attempt = attempt + 1 if attempt < tries else 1
            raise ex

    return wrapper
