import json
import logging
import socket
import sys
import time


import threading
from PyQt5.QtCore import pyqtSignal, QObject

sys.path.append('../')
from utils.config_messages import send_msg, get_msg
from utils.settings import *
from utils.errors import ServerError


LOG = logging.getLogger('client_dist')
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.username = username
        self.transport = None
        self.connection_init(port, ip_address)
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                LOG.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            LOG.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            LOG.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
        self.running = True

    def connection_init(self, port, ip):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.settimeout(5)

        connected = False
        for i in range(3):
            LOG.info(f'Попытка подключения №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:
            LOG.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        LOG.debug('Установлено соединение с сервером')

        try:
            with socket_lock:
                send_msg(self.transport, self.create_presence())
                self.process_server_ans(get_msg(self.transport))
        except (OSError, json.JSONDecodeError):
            LOG.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')
        LOG.info('Соединение с сервером успешно установлено.')

    def create_presence(self):
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.username
            }
        }
        LOG.debug(f'Сформировано {PRESENCE} сообщение для пользователя {self.username}')
        return out

    def process_server_ans(self, message):
        LOG.debug(f'Разбор сообщения от сервера: {message}')

        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            else:
                LOG.debug(f'Принят неизвестный код подтверждения {message[RESPONSE]}')

        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and SENDER in message \
                and DESTINATION in message \
                and MESSAGE_TEXT in message \
                and message[DESTINATION] == self.username:
            LOG.debug(f'Получено сообщение от пользователя {message[SENDER]}:'
                         f'{message[MESSAGE_TEXT]}')
            self.database.save_message(message[SENDER], 'in', message[MESSAGE_TEXT])
            self.new_message.emit(message[SENDER])

    def contacts_list_update(self):
        LOG.debug(f'Запрос контакт листа для пользователя {self.name}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username
        }
        LOG.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_msg(self.transport, req)
            ans = get_msg(self.transport)
        LOG.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            LOG.error('Не удалось обновить список контактов.')

    def user_list_update(self):
        LOG.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            send_msg(self.transport, req)
            ans = get_msg(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.add_users(ans[LIST_INFO])
        else:
            LOG.error('Не удалось обновить список известных пользователей.')

    def add_contact(self, contact):
        LOG.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_msg(self.transport, req)
            self.process_server_ans(get_msg(self.transport))

    def remove_contact(self, contact):
        LOG.debug(f'Удаление контакта {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_msg(self.transport, req)
            self.process_server_ans(get_msg(self.transport))

    def transport_shutdown(self):
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            try:
                send_msg(self.transport, message)
            except OSError:
                pass
        LOG.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    def send_message(self, to, message):
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOG.debug(f'Сформирован словарь сообщения: {message_dict}')

        with socket_lock:
            send_msg(self.transport, message_dict)
            self.process_server_ans(get_msg(self.transport))
            LOG.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        LOG.debug('Запущен процесс - приёмник сообщений с сервера.')
        while self.running:
            time.sleep(1)
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_msg(self.transport)
                except OSError as err:
                    if err.errno:
                        LOG.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, json.JSONDecodeError, TypeError):
                    LOG.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                else:
                    LOG.debug(f'Принято сообщение с сервера: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)
