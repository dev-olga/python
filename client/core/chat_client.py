import ConfigParser
import logging
import os
import select
import socket
import sys
import uuid

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(here, '../../utilities')))
from utilities import message
from utilities import models
from utilities import helpers
import PyQt4.QtGui
import PyQt4.QtCore
from client.ui import login
from client.ui import chat
from client.ui import error_message

class ChatClient():

    _client_socket = None
    _chat_window = None
    _user = None
    _requests = {}
    _listener = None

    @property
    def _logger(self):
        return self.__logger

    @property
    def _config(self):
        return self.__config

    def __init__(self):
        self.__logger = logging.getLogger(__name__)
        self.__config = Configuration('chat_client.cfg')

    def start(self):
        """
        Creates connection to server, opens login window and main window
        """

        # Create PyQt application
        app = PyQt4.QtGui.QApplication(sys.argv)

        # Create socket
        try:
            self._client_socket = self._create_socket()
        except Exception as ex:
            self._logger.exception(ex)
            error_message.ConnectionIsFailed(None)
            sys.exit()

        # Create socket listener
        self._listener = ListenerThread(target=self.listen)
        self._listener.start()

        # Create login window
        login_window = login.LoginWindow(self)
        # Connect login window to the socket listener
        login_window.connect(self._listener, PyQt4.QtCore.SIGNAL('listener_signal'), self._window_listener)

        if login_window.exec_() == PyQt4.QtGui.QDialog.Accepted:
            self._user = models.User()
            self._user.guest = login_window.user.guest
            self._user.login = login_window.user.login
            self._user.user_id = login_window.user.user_id

            login_window.disconnect(self._listener, PyQt4.QtCore.SIGNAL('listener_signal'), self._window_listener)
            del login_window

            # Create main window
            self._chat_window = chat.ChatWindow(self, self._user)

            #  Init user's actions
            self._actions = {
                message.Actions.SERVER_MESSAGE: self._chat_window.server_message,
                message.Actions.USER_MESSAGE: self._chat_window.user_message,
                message.Actions.NEW_USER_IN_CHAT: self._chat_window.add_user,
                message.Actions.USER_IS_OFFLINE: self._chat_window.remove_user,
                message.Actions.USER_WAS_BANNED: self._chat_window.remove_banned_user,
                message.Actions.USER_WAS_MADE_ADMIN: self._chat_window.update_user_as_admin,
                message.Actions.USER_BAN_VOTE_IS_OPENED: self._chat_window.add_user_ban_vote,
                message.Actions.USER_BAN_VOTE_IS_CLOSED: self._chat_window.close_user_ban_vote,
                message.Actions.VOTE_FOR_USER_BAN: self._chat_window.update_user_ban_vote
            }

            # Connect main window to the socket listener
            self._chat_window.connect(self._listener, PyQt4.QtCore.SIGNAL('listener_signal'), self._window_listener)
            self._chat_window.show()

        sys.exit(app.exec_())

    def _window_listener(self, msg):
        """
        Some magic to change UI from background thread
        :param msg: message from server
        """
        callback = None
        if msg.token:
            try:
                callback = self._requests.pop(msg.token)
            except KeyError:
                self._logger.error("Unknown token {0} for action: {0}".format(msg.token, msg.action))
        else:
            try:
                callback = self._actions[msg.action]
            except KeyError:
                self._logger.error("Unknown action: %s" % msg.action)

        if callback:
            if type(msg.arguments) == tuple:
                callback(*msg.arguments)
            else:
                callback(msg.arguments)

    def authorize(self, login, password, guest, callback=None):
        """
        Authorizes user
        :param callback: Callback
        """
        model = models.Authorization()
        model.guest = guest
        model.login = login
        model.password = password

        msg = message.Message()
        msg.action = message.Actions.AUTHORIZE_USER
        msg.token = int(uuid.uuid4())
        msg.arguments = model
        if callback:
            self._requests[msg.token] = callback
        self._send_message(self._client_socket, msg)

    def register(self, login, password, callback):
        """
        Registers user
        :param callback: Callback
        """
        model = models.Registration()
        model.login = login
        model.password = password

        msg = message.Message()
        msg.action = message.Actions.REGISTER_USER
        msg.token = int(uuid.uuid4())
        msg.arguments = model
        if callback:
            self._requests[msg.token] = callback
        self._send_message(self._client_socket, msg)

    def create_chat(self, name, opened, private, password="", callback=None):
        """
        Creates new chat
        :param callback: Callback
        """
        model = models.ChatCreation()
        model.name = name
        model.opened = opened
        model.private = private
        model.password = password

        msg = message.Message()
        msg.action = message.Actions.CREATE_CHAT
        msg.token = int(uuid.uuid4())
        msg.arguments = model
        if callback:
            self._requests[msg.token] = callback
        self._send_message(self._client_socket, msg)

    def enter_chat(self, chat_id, password="", callback=None):
        """
        Authorizes user in the chat
        :param callback: Callback
        """
        model = models.ChatAuthorization()
        model.chat_id = chat_id
        model.password = password
        msg = message.Message()
        msg.action = message.Actions.ENTER_CHAT
        msg.token = int(uuid.uuid4())
        msg.arguments = model
        if callback:
            self._requests[msg.token] = callback
        self._send_message(self._client_socket, msg)

    def load_chats(self, callback=None):
        """
        Loads list of chats
        :param callback: Callback
        """
        msg = message.Message()
        msg.action = message.Actions.CHATS_LIST
        msg.token = int(uuid.uuid4())
        msg.arguments = None
        if callback:
            self._requests[msg.token] = callback
        self._send_message(self._client_socket, msg)

    def send_message(self, chat_id, user_message):
        """
        Sends user's message
        :param chat_id: Chat id
        :param user_message: User message
        """
        msg = message.Message()
        msg.action = message.Actions.USER_MESSAGE

        model = models.UserMessage()
        model.chat_id = chat_id
        model.message = user_message

        msg.arguments = model
        self._send_message(self._client_socket, msg)

    def ban_user(self, chat_id, user_id):
        """
        Bans user in the chat
        :param chat_id: Chat id
        :param user_id: Banned user id
        """
        msg = message.Message()
        msg.action = message.Actions.BAN_USER
        model = models.Ban()
        model.banned_user_id = user_id
        model.chat_id = chat_id
        msg.arguments = model
        self._send_message(self._client_socket, msg)

    def create_ban_vote(self, chat_id, user_id):
        """
        Initializes ban vote
        :param chat_id: Chat id
        :param user_id: Id of the user, that must be banned
        """
        msg = message.Message()
        msg.action = message.Actions.OPEN_USER_BAN_VOTE
        model = models.Ban()
        model.banned_user_id = user_id
        model.chat_id = chat_id
        msg.arguments = model
        self._send_message(self._client_socket, msg)

    def leave_chat(self, chat_id):
        """
        Leaves chat
        :param chat_id: Chat id
        """
        msg = message.Message()
        msg.action = message.Actions.LEAVE_CHAT
        msg.arguments = chat_id
        self._send_message(self._client_socket, msg)

    def make_admin(self, chat_id, user_id):
        """
        Makes user admin of the chat
        :param chat_id: Chat id
        :param user_id: User id that must be made admin
        """
        msg = message.Message()
        msg.action = message.Actions.MAKE_ADMIN
        model = models.UserChatPair()
        model.user_id = user_id
        model.chat_id = chat_id
        msg.arguments = model
        self._send_message(self._client_socket, msg)

    def vote_for_ban(self, chat_id, user_id):
        """
        Votes for user's ban
        :param chat_id: Chat id
        :param user_id: Id of the user, that must be banned
        """
        msg = message.Message()
        msg.action = message.Actions.VOTE_FOR_USER_BAN
        model = models.UserChatPair()
        model.user_id = user_id
        model.chat_id = chat_id
        msg.arguments = model
        self._send_message(self._client_socket, msg)

    def _create_socket(self):
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_socket.connect((self._config.host, self._config.port))
        new_socket.setblocking(0)
        return new_socket

    def _send_message(self, socket, msg):
        try:
            socket.send(message.serialize(msg))
        except Exception as ex:
            self._logger.exception(ex)
            raise ServerUnavailableError()

    def listen(self, callback):
        """
        Socket listener
        :param callback: Function that is called when new message is received
        """
        socket_list = [self._client_socket]
        stop = False
        while not stop:
            # Get the list sockets which are readable
            read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])
            if read_sockets:
                sock = read_sockets[0]
                # incoming message from remote server
                data = helpers.read_all(sock, self._config.buffer_size)
                if data:
                    self._logger.info(data)
                    msg = message.deserialize(data)
                else:
                    msg = message.Message()
                    msg.action = message.Actions.SERVER_MESSAGE
                    resp = models.Response()
                    resp.error = True
                    resp.error_code = message.ErrorCodes.SERVER_IS_UNAVAILABLE
                    resp.message = "Server is unavailable."
                    msg.arguments = resp

                    # clear opened sockets
                    self._client_socket.close()
                    self._requests.clear()
                    stop = True
                    self._logger.error("Server is unavailable.")
                try:
                    callback(msg)
                except Exception as ex:
                    self._logger.exception(ex)


class ListenerThread(PyQt4.QtCore.QThread):
    """
    Is used to change UI from background thread
    """

    def __init__(self, target):
        PyQt4.QtCore.QThread.__init__(self)
        self.target = target

    def run(self):
        self.target(self.callback)

    def callback(self, message):
        self.emit(PyQt4.QtCore.SIGNAL('listener_signal'), message)


class ServerUnavailableError(Exception):

    def __init__(self):
        Exception.__init__(self)


class Configuration():
    def __init__(self, file_name):
        self.__config = ConfigParser.RawConfigParser()
        self.__config.read(file_name)

    @property
    def _config(self):
        return self.__config

    @property
    def buffer_size(self):
        return int(self._config.get('Socket', 'buffer'))

    @property
    def port(self):
        return int(self._config.get('Socket', 'port'))

    @property
    def host(self):
        return self._config.get('Socket', 'host')

