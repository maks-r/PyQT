import sys
import logging

if sys.argv[0].find('client') == -1:
    LOG = logging.getLogger('server')
else:
    LOG = logging.getLogger('client')


def log(func):
    def decorated(*args, **kwargs):
        LOG.debug(f'Функция {func.__name__} c параметрами {args}, {kwargs} Вызов из модуля {func.__module__}')
        res = func(*args, **kwargs)
        return res
    return decorated

