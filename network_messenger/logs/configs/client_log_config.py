import logging
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))
#sys.path.append('../')

from utils.settings import *


ROOT = os.path.dirname('../logs/logs_files/')
ROOT = os.path.join(ROOT, 'client.log')


CLIENT_FORMAT = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s %(process)d')

STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(CLIENT_FORMAT)
STREAM_HANDLER.setLevel(logging.ERROR)
STREAM_HANDLER.setLevel(logging.INFO)
CLIENT_LOG = logging.FileHandler(ROOT, encoding='utf-8')
CLIENT_LOG.setFormatter(CLIENT_FORMAT)

LOG = logging.getLogger('client')
LOG.addHandler(STREAM_HANDLER)
LOG.addHandler(CLIENT_LOG)
LOG.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    LOG.info('Информационное сообщение')
    LOG.debug('Отладка')
    LOG.warning('Предупреждение')
    LOG.critical('Критическая ошибка')
    LOG.error('Ошибка')
