from robot.api import logger


def log_message(message: str, level: str = 'INFO', console: bool = True):
    log_switcher = {
        'TRACE': logger.trace,
        'INFO': logger.info,
        'WARN': logger.warn,
        'ERROR': logger.error
    }
    if not level.upper() in log_switcher.keys() or level.upper() == 'INFO':
        logger.info(message, True, console)
    else:
        if level.upper() == 'ERROR':
            logger.info(message, True, console)
        else:
            log_switcher.get(level.upper(), logger.error)(message, True)


def print_version():
    try:
        file = open('VERSION')
        try:
            log_message('Version {}'.format(file.read().strip()))
        except Exception as ex:
            print('Error reading VERSION file. {}'.format(str(ex)))
        finally:
            file.close()
    except Exception as e:
        print('VERSION file not found. {}'.format(str(e)))
