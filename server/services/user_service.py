import pony.orm
from server.data import data_models

@pony.orm.db_session
def does_user_exist(user_id):
    if user_id > 0:
        user = data_models.user.select(lambda u: u.user_id == user_id)[:1]
        return len(user) > 0
    else:
        return False

@pony.orm.db_session
def does_login_exist(login):
    user = data_models.user.select(lambda u: u.login == login)[:1]
    return len(user) > 0