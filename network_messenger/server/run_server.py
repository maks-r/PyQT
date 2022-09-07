# Загрузка сервера
import logs.configs.server_log_config
from server.server_msg import Server, create_parser
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))


def main():
    listen_address, listen_port = create_parser()
    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
