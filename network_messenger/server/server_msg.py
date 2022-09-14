import argparse
import logging
import socket
import threading
import select
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))

import logs.configs.server_log_config
from utils.config_messages import *
from utils.settings import *
from metaclass_server import ServerVerifier
from utils.server_socket_descriptor import Port
from utils.decorators import log
from dbase.server_db import ServerStorage


SERVER_LOG = logging.getLogger('server')
new_connection = False
conflag_lock = threading.Lock()


@log
def create_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.sock = None
        self.addr = listen_address
        self.port = listen_port
        self.database = database
        self.clients = []
        self.messages = []
        self.names = dict()
        super().__init__()

    def init_socket(self):
        SERVER_LOG.info(
            f'Запущен сервер с портом: {self.port}, через адрес: {self.addr}.'
            f'Если адрес не указан, принимаются соединения с любых адресов.')

        sock_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_obj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_obj.bind((self.addr, self.port))
        sock_obj.settimeout(0.5)
        self.sock = sock_obj
        self.sock.listen()

    def main_loop(self):
        self.init_socket()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                SERVER_LOG.info(f'Установлено соединение с: {client_address}')
                self.clients.append(client)

            recovery_list = []
            send_list = []
            error_list = []

            try:
                if self.clients:
                    recovery_list, send_list, error_list = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                SERVER_LOG.error(f'Ошибка работы с сокетами: {err}')

            if recovery_list:
                for msg_client in recovery_list:
                    try:
                        self.client_msg_proc(get_msg(msg_client), msg_client)
                    except:
                        SERVER_LOG.info(f'Клиент {msg_client.getpeername()} отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == msg_client:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(msg_client)

            for msg in self.messages:
                try:
                    self.process_message(msg, send_list)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    SERVER_LOG.info(f'Связь с клиентом с именем {msg[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[msg[DESTINATION]])
                    del self.names[msg[DESTINATION]]
            self.messages.clear()

    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_msg(self.names[message[DESTINATION]], message)
            SERVER_LOG.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                            f'от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            SERVER_LOG.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, отправка сообщения невозможна.')

    def client_msg_proc(self, message, client):
        SERVER_LOG.debug(f'Разбор сообщения от пользователя : {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(
                    message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_msg(client, RESPONSE_200)
                with conflag_lock:
                    new_connection = True
            else:
                response = RESPONSE_400
                response[ERROR] = 'Имя пользователя уже занято.'
                send_msg(client, response)
                self.clients.remove(client)
                client.close()
            return

        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message and self.names[message[SENDER]] == client:
            self.messages.append(message)
            self.database.process_message(message[SENDER], message[DESTINATION])
            return

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            self.database.user_logout(message[ACCOUNT_NAME])
            SERVER_LOG.info(
                f'Клиент {message[ACCOUNT_NAME]} корректно отключился от сервера.')
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with conflag_lock:
                new_connection = True
            return

        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_msg(client, response)

        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_msg(client, RESPONSE_200)

        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_msg(client, RESPONSE_200)

        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            send_msg(client, response)

        else:
            response = RESPONSE_400
            response[ERROR] = 'Ошибка!!! Запрос некорректен.'
            send_msg(client, response)
            return


def print_help():
    print('Поддерживаемые комманды:')
    print('users - список известных пользователей')
    print('connected - список подключённых пользователей')
    print('loghist - история входов пользователя')
    print('exit - завершение работы сервера.')
    print('help - вывод справки по поддерживаемым командам')
