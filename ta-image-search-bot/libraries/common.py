from robot.api import logger
from RPA.Robocloud.Items import Items
import os


def log_message(message, level='INFO', console=True):
    log_switcher = {
        'TRACE': logger.trace,
        'INFO': logger.info,
        'WARN': logger.warn,
        'ERROR': logger.error
    }
    if not level.upper() in log_switcher.keys() or level.upper() == 'INFO':
        log_switcher.get(level.upper(), logger.info)(message, True, console)
    else:
        if level.upper() == 'ERROR':
            logger.info(message, True, console)
        else:
            log_switcher.get(level.upper(), logger.error)(message, True)


def get_settings():
    library = Items()
    library.load_work_item_from_environment()
    search_term = library.get_work_item_variable('searchTerm')
    search_settings = {'url': 'https://images.google.com/?hl=en',
                       'search_section': 'image', 'search_term': search_term}
    return search_settings


def get_screenshot_path(text):
    return (os.path.join(
                os.environ.get("ROBOT_ROOT", os.getcwd()),
                'output',
                text))
