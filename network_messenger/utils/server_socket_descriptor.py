
import logging
import sys


if sys.argv[0].find('client_dist') == -1:
    LOG = logging.getLogger('server_dist')
else:
    LOG = logging.getLogger('client_dist')


class Port:
    def __set__(self, instance, server_port):
        if not 1023 < server_port < 65536:
            LOG.critical(f'Ошибка! Неверный номер порта: {server_port}. Допустимы от 1024 до 65535.')
            exit(1)

        instance.__dict__[self.name] = server_port

    def __set_name__(self, owner, name):
        self.name = name


