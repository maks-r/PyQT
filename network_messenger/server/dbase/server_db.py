from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '../../'))

from utils.settings import *


class ServerStorage:

    class Users:
        def __init__(self, username):
            self.id = None
            self.name = username
            self.last_time_login = datetime.datetime.now()

    class ActiveUsers:
        def __init__(self, user_id, ip_address, port, login_time):
            self.id = None
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time

    class LoginHistory:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    def __init__(self):
        self.database_engine = create_engine(SERVER_DATABASE,
                                             echo=False,
                                             pool_recycle=7200,
                                             connect_args={'check_same_thread': False})
        self.metadata = MetaData()

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime)
                            )

        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )

        user_login_history = Table('Login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String)
                                   )

        self.metadata.create_all(self.database_engine)

        mapper(self.Users, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port):
        print(username, ip_address, port)
        result = self.session.query(self.Users).filter_by(name=username)

        if result.count():
            user = result.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.Users(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUsers(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)
        history = self.LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)
        self.session.commit()

    def user_logout(self, username):
        user = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def users_list(self):
        query = self.session.query(
            self.Users.name,
            self.Users.last_login
        )
        return query.all()

    def active_users_list(self):
        query = self.session.query(
            self.Users.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.Users)
        return query.all()

    def login_history(self, username=None):
        query = self.session.query(self.Users.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.Users)
        if username:
            query = query.filter(self.Users.name == username)
        return query.all()


if __name__ == '__main__':
    test_db = ServerStorage()
    test_db.user_login('Maks', '192.168.1.7', 5050)
    test_db.user_login('Ivan', '192.168.1.2', 7777)

    print(' ---- test_db.active_users_list() ----')
    print(test_db.active_users_list())

    test_db.user_logout('Maks')
    print(' ---- test_db.active_users_list() after logout Maks ----')
    print(test_db.active_users_list())

    print(' ---- test_db.login_history(Maks) ----')
    print(test_db.login_history('Maks'))

    print(' ---- test_db.users_list() ----')
    print(test_db.users_list())
