#Загрузка клиента
import json
import socket
import logs.configs.client_log_config
from datetime import time
import time
from utils.errors import ReqFieldMissingError, ServerError
from utils.config_messages import get_msg, send_msg
from client.client_msg import response_server, user_presence, ClientReader, ClientSender, create_parser
from utils.settings import *
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))

LOG = logging.getLogger('client')


def main():
    print('Добро пожаловать в консольный месседжер.')

    server_address, server_port, client_name = create_parser()

    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

    LOG.info(f'Запущен пользователь: адрес сервера: {server_address}, порт: {server_port}, имя: {client_name}')

    try:
        sock_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_obj.connect((server_address, server_port))
        send_msg(sock_obj, user_presence(client_name))
        answer = response_server(get_msg(sock_obj))
        LOG.info(f'Установлено соединение!Принят ответ от сервера {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        LOG.error('Ошибка декодирования Json строки.')
        exit(1)
    except ServerError as error:
        LOG.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        exit(1)
    except ReqFieldMissingError as missing_error:
        LOG.error(f'В ответе сервера отсутствует необходимое поле ' f'{missing_error.missing_field}')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        LOG.critical(f'Не удалось подключиться к серверу {server_address}:{server_port},отклонен запрос на подключение')
        exit(1)
    else:
        receiver = ClientReader(client_name, sock_obj)
        receiver.daemon = True
        receiver.start()
        user_interface = ClientSender(client_name, sock_obj)
        user_interface.daemon = True
        user_interface.start()
        LOG.debug('Запущены процессы')

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
