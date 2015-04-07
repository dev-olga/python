import authorization
import pony.orm
import models
from server.data import data_models


@pony.orm.db_session
def get_chat(chat_id):
    try:
        chat = data_models.chat[chat_id]
        res = models.Chat()
        res.fill_from_data(chat)
        return res
    except pony.orm.ObjectNotFound:
        return None


@pony.orm.db_session
def get_chat_by_name(name):
    chats = data_models.chat.select(lambda c: c.name == name)[:1]
    if chats:
        res = models.Chat()
        res.fill_from_data(chats[0])
        return res
    return None


@pony.orm.db_session
def get_user_chats(user_id):
    """
    Returns tuple: chat, if user contains in this chat, if user is admin of the chat
    """
    res = []
    if user_id > 0:
        user_chats = pony.orm.select(
            (c,
             pony.orm.exists(a for a in data_models.chat_admin
                             if c.chat_id == a.chat.chat_id and u.user_id == a.user.user_id))
            for c in data_models.chat
            for u in data_models.user
            if u.user_id == user_id and
               (c.opened or
                not pony.orm.exists(b for b in data_models.ban_list
                                    if c.chat_id == b.chat.chat_id and u.user_id == b.user.user_id)))[:]

        for (c, admin) in user_chats:
            chat = models.Chat()
            chat.fill_from_data(c)
            res.append((chat, admin))

    else:
        user_chats = pony.orm.select(c for c in data_models.chat if c.opened)[:]
        for c in user_chats:
            chat = models.Chat()
            chat.fill_from_data(c)
            res.append((chat, False))

    return res


def add_chat(name, opened=1, private=0, password=''):
    salt = ''
    if private:
        salt = authorization.generate_salt()
        password = authorization.get_hashed_password(password, salt)
    else:
        password = ''
    with data_models.db_session:
        chat = data_models.chat(name=name, opened=opened, private=private, password=password, salt=salt)
    data_models.db.commit()
    return get_chat(chat.chat_id)


@pony.orm.db_session
def add_admin_to_chat(user_id, chat_id):
    user = data_models.user[user_id]
    chat = data_models.chat[chat_id]
    data_models.chat_admin(user=user, chat=chat)


@pony.orm.db_session
def is_user_admin(user_id, chat_id):
    user_chat = data_models.chat_admin.select(lambda cu: cu.user.user_id == user_id and cu.chat.chat_id == chat_id)[:1]
    return len(user_chat) > 0


@pony.orm.db_session
def get_admins(chat_id):
    admins = pony.orm.select(cu.user.user_id for cu in data_models.chat_admin if cu.chat.chat_id == chat_id)[:]
    return admins


@pony.orm.db_session
def ban_user(user_id, chat_id):
    user = data_models.user[user_id]
    chat = data_models.chat[chat_id]
    data_models.ban_list(user=user, chat=chat)


@pony.orm.db_session
def is_user_banned(user_id, chat_id):
    banned = data_models.ban_list.select(lambda b: b.user.user_id == user_id and b.chat.chat_id == chat_id)[:1]
    return len(banned) > 0