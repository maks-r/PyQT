import argparse
import logging
import socket
import sys
import json
import os
import threading

sys.path.append(os.path.join(os.getcwd(), '..'))

from utils.errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
import time
import logs.configs.client_log_config
from utils.settings import *
from utils.decorators import log
from utils.config_messages import get_msg, send_msg
from client.metaclass_client import ClientVerifier


LOG = logging.getLogger('client')


class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name
        }

    def create_message(self):
        username = input('Кому хотите отправить сообщение? Введите имя: ')
        message = input('Введите текст сообщения: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: username,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOG.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_msg(self.sock, message_dict)
            LOG.info(f'Отправлено сообщение для пользователя {username}')
        except:
            LOG.critical('Разрыв соединения с сервером.')
            sys.exit(1)

    def user_interactive(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                try:
                    send_msg(self.sock, self.create_exit_message())
                except:
                    pass
                print('Завершение соединения.')
                LOG.info('Завершение работы.')
                time.sleep(0.5)
                break
            else:
                print('Ошибка!!! Команда не распознана. help - вывести команды.')

    def print_help(self):
        print('Основные поддерживаемые команды:')
        print('message - отправить сообщение.')
        print('help - подсказки по командам')
        print('exit - выход')


class ClientReader(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, user_name, sock):
        self.user_name = user_name
        self.sock = sock
        super().__init__()

    def message_from_server(self):
        while True:
            try:
                message = get_msg(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.user_name:
                    print(f'\nПолучено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
                    LOG.info(f'Получено сообщение от пользователя {message[SENDER]}:\n {message[MESSAGE_TEXT]}')
                else:
                    LOG.error(f'Получено некорректное сообщение с сервера: {message}')
            except IncorrectDataRecivedError:
                LOG.error(f'Не удалось декодировать полученное сообщение.')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                LOG.critical(f'Разрыв соединения с сервером.')
                break


@log
def user_presence(user_name):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: user_name
        }
    }
    LOG.debug(f'Сформировано {PRESENCE} сообщение для пользователя {user_name}')
    return out


@log
def response_server(message):
    LOG.debug(f'Разбор сообщения от сервера: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : Соединение установлено'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log
def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        LOG.critical(f'Ошибка! Неверный номер порта: {server_port}. Допустимы от 1024 до 65535')
        sys.exit(1)

    return server_address, server_port, client_name
