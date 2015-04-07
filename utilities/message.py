import jsonpickle


def serialize(msg):
    return jsonpickle.encode(msg)


def deserialize(str):
    return jsonpickle.decode(str)


class Message:
    def __init__(self):
        self.action = 0
        self.token = ""
        self.arguments = {}


class Actions:
    NONE = 0

    #Common
    USER_MESSAGE = 100
    SERVER_MESSAGE = 101
    USER_IS_OFFLINE = 102
    USER_WAS_BANNED = 103
    NEW_USER_IN_CHAT = 104

    BAN_USER = 105
    OPEN_USER_BAN_VOTE = 106
    USER_BAN_VOTE_IS_OPENED = 107
    VOTE_FOR_USER_BAN = 108
    USER_BAN_VOTE_IS_CLOSED = 109

    LEAVE_CHAT = 109
    MAKE_ADMIN = 110
    USER_WAS_MADE_ADMIN = 110

    #Requests
    AUTHORIZE_USER = 200
    REGISTER_USER = 201
    ENTER_CHAT = 202
    CREATE_CHAT = 203
    CHATS_LIST = 204

    #Respons
    RESPONSE = 301
    ENTER_CHAT_RESPONSE = 302
    NEW_CHAT_RESPONSE = 303
    CHATS_LIST_RESPONSE = 304


class ErrorCodes:
    NONE = 0

    #Chat errors
    CHAT_NOT_FOUND = 101
    USER_IS_BANNED = 102
    USER_MUST_BE_AUTHORIZED = 103
    CHAT_ALREADY_EXISTS = 104
    INVALID_CHAT_NAME = 105
    NOT_ENOUGH_PERMISSIONS = 106

    #Auth errors
    USER_AUTHORIZATION_ERROR = 201
    USER_REGISTRATION_ERROR = 202
    CHAT_AUTHORIZATION_ERROR = 302

    #Server errors
    SERVER_IS_UNAVAILABLE = 301
    INTERNAL_SERVER_ERROR = 302

    #Request errors
    UNKNOWN_ACTION = 401



