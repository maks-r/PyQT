import logging

DEFAULT_PORT = 7777
DEFAULT_IP_ADDRESS = '127.0.0.1'

ACTION = 'action'
TIME = 'time'

USER = 'user'
ACCOUNT_NAME = 'account_name'
TYPE = 'type'
STATUS = 'status'
SENDER = 'from'
DESTINATION = 'to'

PRESENCE = 'presence'
RESPONSE = 'response'
MESSAGE = 'message'
MESSAGE_TEXT = 'message_text'
EXIT = 'exit'

ERROR = 'error'

LOGGING_LEVEL = logging.DEBUG


RESPONSE_200 = {RESPONSE: 200}
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}

MAX_CONNECTIONS = 5
MAX_PACKAGE_LENGTH = 1024
ENCODING = 'utf-8'