
class Response(object):
    def __init__(self):
        self.error = False
        self.error_code = 0
        self.message = ""


class User(object):
    def __init__(self):
        self.user_id = 0
        self.login = ""
        self.guest = False


class Registration(object):
    def __init__(self):
        self.login = ""
        self.password = ""


class Authorization(Registration):
    def __init__(self):
        self.login = ""
        self.password = ""
        self.guest = True


class AuthorizationResponse(Response, User):
    def __init__(self):
        Response.__init__(self)
        User.__init__(self)

# Chat models


class Chat(object):
    def __init__(self):
        self.chat_id = 0
        self.name = ""
        self.opened = True
        self.private = False


class ChatCreation(object):
    def __init__(self):
        self.name = ""
        self.opened = True
        self.private = False
        self.password = ""


class CurrentUserChat(Chat):
    def __init__(self):
        super(CurrentUserChat, self).__init__()
        self.admin = False


class ChatResponse(CurrentUserChat, Response):
    def __init__(self):
        CurrentUserChat.__init__(self)
        Response.__init__(self)
        self.users = []


class ChatAuthorization(object):
    def __init__(self):
        self.chat_id = 0
        self.password = ""

#Message models


class BaseMessage(object):
    def __init__(self):
        self.chat_id = 0
        self.message = ""


class UserMessage(BaseMessage):
    def __init__(self):
        super(UserMessage, self).__init__()
        self.user_id = 0
        self.login = ""
        self.guest = False


class UserOfChat(object):
    def __init__(self):
        self.user_id = 0
        self.login = ""
        self.guest = False
        self.admin = False
        self.is_in_ban_vote = False
        self.can_be_voted = False


class Ban(object):
    def _init__(self):
        self.initiator_id = 0
        self.banned_user_id = 0
        self.chat_id = 0


class BanVote(Ban):
    def __init__(self):
        super(BanVote, self).__init__()
        self.timeout = 0


class UserChatPair(object):
    def _init__(self):
        self.user_id = 0
        self.chat_id = 0
