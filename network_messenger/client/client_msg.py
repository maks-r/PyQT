import argparse
import logging
import socket
import json
import threading
import time
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))

from utils.errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError
import logs.configs.client_log_config
from utils.settings import *
from utils.decorators import log
from utils.config_messages import get_msg, send_msg
from metaclass_client import ClientVerifier
from dbase.client_db import ClientDatabase

LOG = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
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

        with database_lock:
            if not self.database.check_user(username):
                LOG.error(f'Попытка отправить сообщение '
                             f'незарегистрированому получателю: {username}')
                return

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: username,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOG.debug(f'Сформирован словарь сообщения: {message_dict}')

        with database_lock:
            self.database.save_message(self.account_name, username, message)

        with sock_lock:
            try:
                send_msg(self.sock, message_dict)
                LOG.info(f'Отправлено сообщение для пользователя {username}')
            except OSError as err:
                if err.errno:
                    LOG.critical('Разрыв соединения с сервером.')
                    sys.exit(1)
                else:
                    LOG.error('Сообщение не отправлено!!!')

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

            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            elif command == 'edit':
                self.edit_contacts()

            elif command == 'history':
                self.print_history()
            else:
                print('Ошибка!!! Команда не распознана. help - вывести команды.')

    def print_help(self):
        print('Основные поддерживаемые команды:')
        print('message - отправить сообщение.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - подсказки по командам')
        print('exit - выход')

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    LOG.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        LOG.error('Не удалось отправить информацию на сервер.')


class ClientReader(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, user_name, sock, database):
        self.user_name = user_name
        self.sock = sock
        self.database = database
        super().__init__()

    def message_from_server(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_msg(self.sock)

                except IncorrectDataRecivedError:
                    LOG.error(f'Не удалось декодировать полученное сообщение.')
                except OSError as err:
                    if err.errno:
                        LOG.critical(f'Потеряно соединение с сервером.')
                        break
                except (ConnectionError,
                        ConnectionAbortedError,
                        ConnectionResetError,
                        json.JSONDecodeError):
                    LOG.critical(f'Потеряно соединение с сервером.')
                    break

                else:
                    if ACTION in message and message[ACTION] == MESSAGE and \
                            SENDER in message and DESTINATION in message \
                            and MESSAGE_TEXT in message and message[DESTINATION] == self.user_name:
                        print(f'\nПолучено сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')

                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER],
                                                           self.user_name,
                                                           message[MESSAGE_TEXT])
                            except Exception as e:
                                print(e)
                                LOG.error('Ошибка взаимодействия с базой данных')

                        LOG.info(f'Получено сообщение от пользователя {message[SENDER]}:\n {message[MESSAGE_TEXT]}')
                    else:
                        LOG.error(f'Получено некорректное сообщение с сервера: {message}')


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


def contacts_list_request(sock, name):
    LOG.debug(f'Запрос контакт листа для пользователя {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    LOG.debug(f'Сформирован запрос {req}')
    send_msg(sock, req)
    ans = get_msg(sock)
    LOG.debug(f'Получен ответ {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def add_contact(sock, username, contact):
    LOG.debug(f'Создание контакта {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_msg(sock, req)
    ans = get_msg(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')


def user_list_request(sock, username):
    LOG.debug(f'Запрос списка известных пользователей {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_msg(sock, req)
    ans = get_msg(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def remove_contact(sock, username, contact):
    LOG.debug(f'Создание контакта {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_msg(sock, req)
    ans = get_msg(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удачное удаление')


def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        LOG.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        LOG.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


# def main():
#     print('Добро пожаловать в консольный месседжер.')
#
#     server_address, server_port, client_name = create_parser()
#
#     if not client_name:
#         client_name = input('Введите имя пользователя: ')
#     else:
#         print(f'Клиентский модуль запущен с именем: {client_name}')
#
#     LOG.info(f'Запущен пользователь: адрес сервера: {server_address}, порт: {server_port}, имя: {client_name}')
#
#     try:
#         sock_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         sock_obj.settimeout(1)
#         sock_obj.connect((server_address, server_port))
#         send_msg(sock_obj, user_presence(client_name))
#         answer = response_server(get_msg(sock_obj))
#         LOG.info(f'Установлено соединение!Принят ответ от сервера {answer}')
#         print(f'Установлено соединение с сервером.')
#     except json.JSONDecodeError:
#         LOG.error('Ошибка декодирования Json строки.')
#         exit(1)
#     except ServerError as error:
#         LOG.error(f'При установке соединения сервер вернул ошибку: {error.text}')
#         exit(1)
#     except ReqFieldMissingError as missing_error:
#         LOG.error(f'В ответе сервера отсутствует необходимое поле ' f'{missing_error.missing_field}')
#         exit(1)
#     except (ConnectionRefusedError, ConnectionError):
#         LOG.critical(f'Не удалось подключиться к серверу {server_address}:{server_port},отклонен запрос на подключение')
#         exit(1)
#     else:
#         database = ClientDatabase(client_name)
#         database_load(sock_obj, database, client_name)
#         receiver = ClientReader(client_name, sock_obj, database)
#         receiver.daemon = True
#         receiver.start()
#         LOG.debug('Запущены процессы')
#         user_interface = ClientSender(client_name, sock_obj, database)
#         user_interface.daemon = True
#         user_interface.start()
#
#
#         while True:
#             time.sleep(1)
#             if receiver.is_alive() and user_interface.is_alive():
#                 continue
#             break
#
#     #x = input()
#
#
# if __name__ == '__main__':
#     main()