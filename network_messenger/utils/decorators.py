# -*- coding: utf-8 -*-

import sys
import logs.client_log_config
import logs.server_log_config
import logging

if sys.argv[0].find('client_dist') == -1:
    LOG = logging.getLogger('server_dist')
else:
    LOG = logging.getLogger('client_dist')


def log(func):
    def decorated(*args, **kwargs):
        LOG.debug(f'Функция {func.__name__} c параметрами {args}, {kwargs} Вызов из модуля {func.__module__}')
        res = func(*args, **kwargs)
        return res
    return decorated