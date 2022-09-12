import dis


class ServerVerifier(type):
    def __init__(cls, name, bases, dict):
        GLOBAL = []
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
                        if i.argval not in GLOBAL:
                            GLOBAL.append(i.argval)
                    elif i.opname == 'LOAD_METHOD':
                        if i.argval not in METHOD:
                            METHOD.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in ATTR:
                            ATTR.append(i.argval)
        if 'connect' in GLOBAL:
            raise TypeError('Использование метода connect недопустимо в серверном классе')
        if not ('SOCK_STREAM' in ATTR and 'AF_INET' in ATTR):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(name, bases, dict)