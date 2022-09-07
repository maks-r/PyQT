import subprocess


p_list = []

while True:
    ACTION = input('Для запуска сервера нажмите - s, выйти - q, закрыть окно - x: ')

    if ACTION == 'q':
        break
    elif ACTION == 's':
        p_list.append(subprocess.Popen('python run_server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif ACTION == 'x':
        while p_list:
            VICTIM = p_list.pop()
            VICTIM.kill()