import sys
import logging
import inspect


def log(func):
    def decorated(*args, **kwargs):
        res = func(*args, **kwargs)
        if sys.argv[0].find('client') == -1:
            LOG = logging.getLogger('server')
        else:
            LOG = logging.getLogger('client')
        LOG.debug(f'Функция {func.__name__} {args}, {kwargs} вызвана из функции {inspect.stack()[1][3]}', stacklevel=2)
        return res
    return decorated

