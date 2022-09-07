import logging.handlers
import sys
import os
from utils.settings import *

sys.path.append('../')

ROOT = os.path.dirname('../logs/logs_files/')
ROOT = os.path.join(ROOT, 'server.log')

CLIENT_FORMAT = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s %(process)d')

STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(CLIENT_FORMAT)
STREAM_HANDLER.setLevel(logging.ERROR)
STREAM_HANDLER.setLevel(logging.INFO)
CLIENT_LOG = logging.handlers.TimedRotatingFileHandler(ROOT, encoding='utf8', interval=1, when='midnight')
CLIENT_LOG.setLevel(logging.INFO)
CLIENT_LOG.setLevel(logging.DEBUG)
CLIENT_LOG.setFormatter(CLIENT_FORMAT)

LOG = logging.getLogger('server')
LOG.addHandler(STREAM_HANDLER)
LOG.addHandler(CLIENT_LOG)
LOG.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    LOG.info('Информационное сообщение')
    LOG.debug('Отладка')
    LOG.warning('Предупреждение')
    LOG.critical('Критическая ошибка')
    LOG.error('Ошибка')