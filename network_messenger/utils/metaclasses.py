# -*- coding: utf-8 -*-

import dis


class ServerVerifier(type):
    def __init__(cls, name, bases, dict):
        METHOD = []
        ATTR = []
        for func in dict:
            try:
                ret = dis.get_instructions(dict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in METHOD:
                            METHOD.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in ATTR:
                            ATTR.append(i.argval)
        if 'connect' in METHOD:
            raise TypeError('Использование метода connect недопустимо в серверном классе')
        if not ('SOCK_STREAM' in ATTR and 'AF_INET' in ATTR):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(name, bases, dict)


class ClientVerifier(type):
    def __init__(cls, name, bases, dict):
        methods = []
        for func in dict:
            try:
                ret = dis.get_instructions(dict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('В классе обнаружено использование запрещённого метода')
        if 'get_msg' in methods or 'send_msg' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
        super().__init__(name, bases, dict)


