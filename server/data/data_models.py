from pony.orm import *
from datetime import datetime


db = Database('sqlite', 'database', create_db=True)


class user(db.Entity):
    user_id = PrimaryKey(int, auto=True)
    login = Required(str)
    password = Required(str)
    salt = Required(str)
    chats = Set("chat_admin")
    bans = Set("ban_list")


class chat(db.Entity):
    chat_id = PrimaryKey(int, auto=True)
    name = Required(str)
    opened = Required(int, default=1)
    private = Required(int, default=0)
    password = Optional(str)
    salt = Optional(str)
    admins = Set("chat_admin")
    bans = Set("ban_list")

# class user_chat(db.Entity):
#     user_chat_id = PrimaryKey(int, auto=True)
#     admin = Required(int, default=0)
#     user = Required("user")
#     chat = Required("chat")


class chat_admin(db.Entity):
    chat_admin_id = PrimaryKey(int, auto=True)
    user = Required("user")
    chat = Required("chat")


class ban_list(db.Entity):
    ban_list_id = PrimaryKey(int, auto=True)
    chat = Required("chat")
    user = Required("user")
    # user_id = Optional(int)
    # login = Optional(str)
    # expiration_date = Required(datetime)




db.generate_mapping(create_tables=True)