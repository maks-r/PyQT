import argparse
import logging
import socket
import select
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))

import logs.configs.server_log_config
from utils.config_messages import send_msg, get_msg
from utils.settings import *
from server.metaclass_server import ServerVerifier
from utils.server_socket_descriptor import Port
from utils.decorators import log

SERVER_LOG = logging.getLogger('server')


@log
def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
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
            except OSError:
                pass

            if recovery_list:
                for msg_client in recovery_list:
                    try:
                        self.client_msg_proc(get_msg(msg_client), msg_client)
                    except:
                        SERVER_LOG.info(f'Клиент {msg_client.getpeername()} отключился от сервера.')
                        self.clients.remove(msg_client)

            for msg in self.messages:
                try:
                    self.process_message(msg, send_list)
                except:
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
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_msg(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Ошибка!!! Имя занято.'
                send_msg(client, response)
                self.clients.remove(client)
                client.close()
            return
        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
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
