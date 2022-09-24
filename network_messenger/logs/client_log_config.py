# -*- coding: utf-8 -*-

import logging
import sys
import os
sys.path.append('../')

from utils.settings import LOGGING_LEVEL


CLIENT_FORMAT = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s %(process)d')

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(ROOT, 'logs_files/client.log')

STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(CLIENT_FORMAT)
STREAM_HANDLER.setLevel(logging.ERROR)
STREAM_HANDLER.setLevel(logging.INFO)
CLIENT_LOG = logging.FileHandler(ROOT, encoding='utf-8')
CLIENT_LOG.setFormatter(CLIENT_FORMAT)

LOG = logging.getLogger('client_dist')
LOG.addHandler(STREAM_HANDLER)
LOG.addHandler(CLIENT_LOG)
LOG.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    LOG.info('Информационное сообщение')
    LOG.debug('Отладка')
    LOG.warning('Предупреждение')
    LOG.critical('Критическая ошибка')
    LOG.error('Ошибка')