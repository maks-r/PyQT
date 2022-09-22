# -*- coding: utf-8 -*-
import logging
import socket
import sys
sys.path.append('../')
import logs.client_log_config
import logs.server_log_config


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


def login_required(func_req):
    def checker(*args, **kwargs):
        from server.core import MessageProcessor
        from utils.settings import ACTION, PRESENCE
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True

            if not found:
                raise TypeError
        return func_req(*args, **kwargs)

    return checker