# Загрузка сервера
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))
import logs.configs.server_log_config
from server.server_msg import Server, create_parser, print_help
from server.dbase.server_db import ServerStorage


def main():
    listen_address, listen_port = create_parser()
    database = ServerStorage()
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.main_loop()

    print_help()

 # Основной цикл сервера:
    while True:
        command = input('Введите команду: ')
        if command == 'help':
            print_help()
        elif command == 'exit':
            break
        elif command == 'users':
            all_users = sorted(database.users_list())
            if all_users:
                for user in all_users:
                    print(f'Пользователь {user[0]}, последний вход: {user[1]}')
            else:
                print('No data')

        elif command == 'connected':
            active_users = sorted(database.active_users_list())
            if active_users:
                for user in active_users:
                    print(f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, '
                          f'время установки соединения: {user[3]}')
            else:
                print('No data')
        elif command == 'loghist':
            name = input('Введите имя пользователя для просмотра истории. '
                         'Для вывода всей истории, просто нажмите Enter: ')
            history = sorted(database.login_history(name))
            if history:
                for user in sorted(database.login_history(name)):
                    print(f'Пользователь: {user[0]} время входа: {user[1]}. '
                          f'Вход с: {user[2]}:{user[3]}')
            else:
                print('No data')
        else:
            print('Команда не распознана.')


if __name__ == '__main__':
    main()
