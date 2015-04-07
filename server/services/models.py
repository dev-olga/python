class Chat():

    def fill_from_data(self, chat):
        self.chat_id = chat.chat_id
        self.name = chat.name
        self.opened = chat.opened
        self.private = chat.private
        self.password = chat.password
        self.salt = chat.salt

    chat_id = 0
    name = ""
    opened = True
    private = False
    password = ""
    salt = ""


class UserChat():

    def fill_from_data(self, user_chat, admin=0):
        self.user_chat_id = user_chat.user_chat_id
        self.admin = admin
        self.user_id = user_chat.user.user_id
        self.chat_id = user_chat.chat.chat_id

    user_chat_id = 0
    admin = 0
    user_id = 0
    chat_id = 0