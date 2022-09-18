import subprocess
import os
import sys

sys.path.append('../')

proc_list = []

while True:
    ACTION = input('Для запуска клиента нажмите - s, для выхода - q, закрыть окно - x: ')
    if ACTION == 'q':
        break
    elif ACTION == 's':
        clients = int(input('Введите количество тестовых клиентов для запуска: '))
        proc_list.append(subprocess.Popen('python run_server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(clients):
            proc_list.append(subprocess.Popen(f'python run_client.py -n test{i + 1}',
                                              creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif ACTION == 'x':
        while proc_list:
            proc_list.pop().kill()
