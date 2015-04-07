import hashlib
import string
import random

import pony.orm

from server.data import data_models


@pony.orm.db_session
def user_authorization(login, password):
    users = data_models.user.select(lambda u: u.login == login)[:1]
    if users:
        user = users[0]
        if user.password == get_hashed_password(password, user.salt):
            return True, user.user_id
    return False, 0


def user_registration(login, password):
    salt = generate_salt()
    password = get_hashed_password(password, salt)
    with data_models.db_session:
        user = data_models.user(login=login, password=password, salt=salt)
    data_models.db.commit()
    return user.user_id


@pony.orm.db_session
def chat_authorization(chat_id, password):
    chats = data_models.chat.select(lambda c: c.chat_id == chat_id)[:1]
    if chats:
        chat = chats[0]
        if chat.password == get_hashed_password(password, chat.salt):
            return True
    return False


def generate_salt():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))


def get_hashed_password(password, salt):
    m = hashlib.md5()
    m.update(password + salt)
    return m.hexdigest()