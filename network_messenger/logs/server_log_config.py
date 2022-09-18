# -*- coding: utf-8 -*-

import logging.handlers
import sys
import os
sys.path.append('../')

from utils.settings import LOGGING_LEVEL


SERVER_FORMAT = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s %(process)d')

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(ROOT, 'logs_files/server.log')

STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(SERVER_FORMAT)
STREAM_HANDLER.setLevel(logging.ERROR)
STREAM_HANDLER.setLevel(logging.INFO)
SERVER_LOG = logging.handlers.TimedRotatingFileHandler(ROOT, encoding='utf8', interval=1, when='D')
SERVER_LOG.setLevel(logging.INFO)
SERVER_LOG.setLevel(logging.DEBUG)
SERVER_LOG.setFormatter(SERVER_FORMAT)

LOG = logging.getLogger('server_dist')
LOG.addHandler(STREAM_HANDLER)
LOG.addHandler(SERVER_LOG)
LOG.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    LOG.info('Информационное сообщение')
    LOG.debug('Отладка')
    LOG.warning('Предупреждение')
    LOG.critical('Критическая ошибка')
    LOG.error('Ошибка')

