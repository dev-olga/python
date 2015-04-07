import ConfigParser
import logging
import operator
import os
import select
import socket
import sys

import server.services.authorization
import server.services.chat_service
import server.services.user_service

from session_provider import SessionProvider
from vote import VoteManager
from active_chats import ActiveChatsManager

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(here, '../../utilities')))
from utilities import message
from utilities import models
from utilities import helpers


class ChatServer(object):
    _server_socket = None

    @property
    def _actions(self):
        return self.__actions

    @property
    def _connections(self):
        """
        Connected sockets. Key is socket, Type is SessionProvider
        """
        return self.__connections

    @property
    def _active_chats(self):
        """
        Active chats. Key is chat_id. Type is ActiveChats
        """
        return self.__opened_rooms

    @property
    def _active_ban_votes(self):
        """
        Active ban votes. Key is (chat_id, user_id). Type is VoteManager
        """
        return self.__active_ban_votes

    @property
    def _logger(self):
        return self.__logger

    @property
    def _config(self):
        return self.__config

    def __init__(self):
        self.__actions = {message.Actions.AUTHORIZE_USER: self._authorize,
                          message.Actions.REGISTER_USER: self._register,
                          message.Actions.CHATS_LIST: self._load_chats,
                          message.Actions.ENTER_CHAT: self._enter_room,
                          message.Actions.CREATE_CHAT: self._create_chat,
                          message.Actions.BAN_USER: self._try_to_ban_user,
                          message.Actions.USER_MESSAGE: self._send_user_message,
                          message.Actions.LEAVE_CHAT: self._remove_user_from_chat,
                          message.Actions.MAKE_ADMIN: self._make_admin,
                          message.Actions.OPEN_USER_BAN_VOTE: self._open_user_ban_vote,
                          message.Actions.VOTE_FOR_USER_BAN: self._vote_for_user_ban}

        self.__logger = logging.getLogger(__name__)
        self.__connections = SessionProvider()
        self.__opened_rooms = ActiveChatsManager()
        self.__active_ban_votes = VoteManager()

        self.__config = Configuration('chat_server.cfg')

    def start(self):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self._config.host, self._config.port))
        # self._server_socket.listen(10)
        self._server_socket.listen(0)

        # Add server socket to the list of readable connections
        server_session = Session()
        server_session.address = self._config.host
        self._connections.add_session(self._server_socket, server_session)

        while 1:
            # Get the list sockets which are ready to be read through select
            read_sockets, write_sockets, error_sockets = select.select(self._connections.get_keys(), [], [])

            for sock in read_sockets:
                #New connection
                if sock == self._server_socket:
                    # Handle the case in which there is a new connection received through server_socket
                    sockfd, address = self._server_socket.accept()
                    sockfd.setblocking(0)
                    userSession = Session()
                    userSession.address = address
                    self._connections.add_session(sockfd, userSession)
                    self._logger.info("Client (%s, %s) connected" % address)

                #Some incoming message from a client
                else:
                    try:
                        self._process(sock)
                    except EmptyDataError:
                        session = self._connections.get_session(sock)
                        if session:
                            server_message = message.Message()
                            server_message.action = message.Actions.USER_IS_OFFLINE
                            user = models.User()
                            user.user_id = session.user_id
                            user.guest = session.is_guest
                            user.login = session.login

                            rooms = self._active_chats.get_keys()
                            for room in rooms:
                                if sock in self._active_chats.get(room):
                                    server_message.arguments = (room, user)
                                    self._remove_socket_from_room(room, sock)
                                    self._broadcast(room, server_message, sock)
                        self._connections.remove_session(sock)
                        self._logger.info("Client (%s, %s) is offline" % session.address)
                        try:
                            sock.close()
                        finally:
                            pass

                    except Exception as ex:
                        self._logger.exception(ex)

        self._server_socket.close()

    def _process(self, socket):
        data = helpers.read_all(socket, self._config.buffer_size)
        if data:
            msg = message.deserialize(data)
            try:
                action = self._actions[msg.action]
                action(socket, msg.arguments, msg.token)
            except KeyError:
                msg = message.Message()
                msg.action = message.Actions.SERVER_MESSAGE
                resp = models.Response()
                resp.error = True
                resp.error_code = message.ErrorCodes.UNKNOWN_ACTION
                resp.message = "Unknown action."
                msg.arguments = resp
                self._try_send(socket, message.serialize(msg))
            except Exception as ex:
                msg = message.Message()
                msg.action = message.Actions.SERVER_MESSAGE
                resp = models.Response()
                resp.error = True
                resp.error_code = message.ErrorCodes.INTERNAL_SERVER_ERROR
                resp.message = "Internal server error."
                msg.arguments = resp
                self._try_send(socket, message.serialize(msg))
                self._logger.exception(ex)
        else:
            raise EmptyDataError()

    def _authorize(self, socket, model, token=""):
        """
        Authorize user
        :param socket: user's socket
        :param model: user's auth data. Type models.Authorization
        :param token: response token
        """
        session = self._connections.get_session(socket)
        resp = message.Message()
        resp.action = message.Actions.RESPONSE
        resp_model = models.AuthorizationResponse()

        if not model.login:
            resp_model.error = True
            resp_model.error_code = message.ErrorCodes.USER_AUTHORIZATION_ERROR
            resp_model.message = "Login cannot be empty string"
        elif model.guest:
            keys = self._connections.get_keys()
            is_used = False
            for key in keys:
                s = self._connections.get_session(key)
                is_used = s.login == model.login and s.is_guest
                if is_used:
                    break

            if is_used:
                resp_model.error = True
                resp_model.error_code = message.ErrorCodes.USER_AUTHORIZATION_ERROR
                resp_model.message = "User with the same login is already online."
            else:
                session.is_guest = True
                session.login = model.login

                resp_model.login = session.login
                resp_model.guest = session.is_guest

                resp_model.error = False
        else:
            valid, user_id = server.services.authorization.user_authorization(model.login, model.password)
            if valid:
                session.user_id = user_id
                session.is_guest = False
                session.login = model.login

                resp_model.error = False
                resp_model.user_id = session.user_id
                resp_model.login = session.login
                resp_model.guest = session.is_guest
            else:
                resp_model.error = True
                resp_model.error_code = message.ErrorCodes.USER_AUTHORIZATION_ERROR
                resp_model.message = "Invalid login or password"

        resp.token = token
        resp.arguments = resp_model
        self._try_send(socket, message.serialize(resp))

    def _register(self, socket, model, token=""):
        """
        Register user
        :param socket: user's socket
        :param model: user's registration data. Type is models.Registration
        :param token: response token
        """
        session = self._connections.get_session(socket)
        resp = message.Message()
        resp.action = message.Actions.RESPONSE
        resp_model = models.AuthorizationResponse()

        if model.login:
            is_used = server.services.user_service.does_login_exist(model.login)
            user_id = server.services.authorization.user_registration(model.login, model.password)

            if is_used:
                resp_model.error = True
                resp_model.error_code = message.ErrorCodes.USER_REGISTRATION_ERROR
                resp_model.message = "User with the same login is already registered."
            else:
                session.user_id = user_id
                session.is_guest = False
                session.login = model.login

                resp_model.user_id = session.user_id
                resp_model.login = session.login
                resp_model.guest = session.is_guest

                resp_model.error = False
        else:
            resp_model.error = True
            resp_model.error_code = message.ErrorCodes.USER_REGISTRATION_ERROR
            resp_model.message = "Login cannot be empty string"

        resp.token = token
        resp.arguments = resp_model
        self._try_send(socket, message.serialize(resp))

    def _load_chats(self, socket, model=None, token=""):
        """
        Load list of available chats
        :param socket: user's socket
        :param token: response token
        """
        session = self._connections.get_session(socket)
        chats = server.services.chat_service.get_user_chats(session.user_id)
        resp = message.Message()
        resp.action = message.Actions.CHATS_LIST_RESPONSE
        resp.token = token
        resp_model = []
        for (c, admin) in chats:
            m = models.CurrentUserChat()
            m.admin = admin
            m.chat_id = c.chat_id
            m.name = c.name
            m.opened = c.opened
            m.private = c.private
            resp_model.append(m)
            resp_model.sort(key=operator.attrgetter('name'))
        resp.arguments = resp_model
        self._try_send(socket, message.serialize(resp))

    def _enter_room(self, socket, model, token=""):
        """
        Authorize users in the chat
        :param socket:user's socket
        :param model: chat authorization data. Type is models.ChatAuthorization
        :param token: response token
        """
        session = self._connections.get_session(socket)
        chat = server.services.chat_service.get_chat(model.chat_id)
        resp = message.Message()
        resp.action = message.Actions.ENTER_CHAT_RESPONSE
        resp_model = models.ChatResponse()
        if not chat is None:
            #check if user was banned.
            is_banned = not session.is_guest \
                and server.services.chat_service.is_user_banned(session.user_id, chat.chat_id)
            if is_banned:
                resp_model.error = True
                resp_model.error_code = message.ErrorCodes.USER_IS_BANNED
                resp_model.message = "User is banned"
            elif not chat.opened and session.is_guest:
                resp_model.error = True
                resp_model.error_code = message.ErrorCodes.USER_MUST_BE_AUTHORIZED
                resp_model.message = "Only authorized users can enter this chat"

            if not resp_model.error and chat.private:
                if not server.services.authorization.chat_authorization(model.chat_id, model.password):
                    resp_model.error = True
                    resp_model.error_code = message.ErrorCodes.CHAT_AUTHORIZATION_ERROR
                    resp_model.message = "Chat authorization error"

            if not resp_model.error:
                resp_model.error = False
                resp_model.chat_id = chat.chat_id
                resp_model.name = chat.name
                resp_model.opened = chat.opened
                resp_model.private = chat.private
                resp_model.admin = server.services.chat_service.is_user_admin(session.user_id, chat.chat_id)

                resp_model.users = []
                admins = server.services.chat_service.get_admins(chat.chat_id)

                self._active_chats.add(chat.chat_id, socket)
                for s in self._active_chats.get(chat.chat_id):
                    if s != socket:
                        chat_member = self._connections.get_session(s)
                        user = models.UserOfChat()
                        user.user_id = chat_member.user_id
                        user.login = chat_member.login
                        user.admin = chat_member.user_id in admins
                        user.guest = chat_member.is_guest
                        user.is_in_ban_vote = self._active_ban_votes.has_key((model.chat_id, chat_member.user_id))
                        user.can_be_voted = user.is_in_ban_vote
                        resp_model.users.append(user)

                user = models.UserOfChat()
                user.user_id = session.user_id
                user.login = session.login
                user.admin = session.user_id in admins
                user.guest = session.is_guest
                server_message = message.Message()
                server_message.action = message.Actions.NEW_USER_IN_CHAT
                server_message.arguments = (chat.chat_id, user)
                self._broadcast(chat.chat_id, server_message, socket)

        else:
            resp_model.error = True
            resp_model.error_code = message.ErrorCodes.CHAT_NOT_FOUND

        resp.token = token
        resp.arguments = resp_model
        self._try_send(socket, message.serialize(resp))

    def _send_user_message(self, socket, model, token=""):
        """
        Broadcast user's message
        :param socket: user's socket
        :param model: message. Type is models.BaseMessage
        :param token: response token
        """
        session = self._connections.get_session(socket)
        if socket in self._active_chats.get(model.chat_id):
            msg = message.Message()
            msg.action = message.Actions.USER_MESSAGE
            resp_model = models.UserMessage()
            resp_model.chat_id = model.chat_id
            resp_model.message = model.message
            resp_model.user_id = session.user_id
            resp_model.login = session.login
            resp_model.guest = session.is_guest
            msg.arguments = resp_model

            self._broadcast(model.chat_id, msg, socket)
        else:
            resp_model = models.Response()
            resp_model.error = True
            resp_model.error_code = message.ErrorCodes.NOT_ENOUGH_PERMISSIONS
            resp_model.message = "You aren't member of the chat."
            resp = message.Message()
            resp.action = message.Actions.RESPONSE
            resp.arguments = resp_model
            resp.token = token
            self._try_send(resp_model)

    def _create_chat(self, socket, model, token=""):
        """
        Create new chat
        :param socket: user's socket
        :param model: new chat data. Type is models.ChatCreation
        :param token: response token
        """
        resp = message.Message()
        resp_model = None

        valid = True
        if not model.name:
            resp.action = message.Actions.RESPONSE
            resp_model = models.Response()
            resp_model.error = True
            resp_model.message = "Chat name cannot be empty string."
            resp_model.error_code = message.ErrorCodes.INVALID_CHAT_NAME
            valid = False

        if valid:
            session = self._connections.get_session(socket)
            if session.is_guest and not model.opened:
                resp.action = message.Actions.RESPONSE
                resp_model = models.Response()
                resp_model.error = True
                resp_model.message = "Only authorized users can create not opened chats"
                resp_model.error_code = message.ErrorCodes.NOT_ENOUGH_PERMISSIONS
                valid = False

        if valid and (not server.services.chat_service.get_chat_by_name(model.name) is None):
            resp.action = message.Actions.RESPONSE
            resp_model = models.Response()
            resp_model.error = True
            resp_model.message = "Chat with name " + model.name + " already exists"
            resp_model.error_code = message.ErrorCodes.CHAT_ALREADY_EXISTS
            valid = False

        if valid:
            chat = server.services.chat_service.add_chat(model.name, model.opened, model.private, model.password)
            if not session.is_guest and not model.opened:
                server.services.chat_service.add_admin_to_chat(session.user_id, chat.chat_id)

            resp.action = message.Actions.NEW_CHAT_RESPONSE
            resp_model = models.ChatResponse()
            resp_model.error = False
            resp_model.chat_id = chat.chat_id
            resp_model.name = chat.name
            resp_model.opened = chat.opened
            resp_model.private = chat.private

        resp.token = token
        resp.arguments = resp_model
        self._try_send(socket, message.serialize(resp))

    def _try_to_ban_user(self, socket, model, token=""):
        """
        User's ban request
        :param socket: socket of the users who want to ban other user
        :param model: ban model
        :param token: response token
        """
        resp = message.Message()
        session = self._connections.get_session(socket)
        admin = server.services.chat_service.is_user_admin(session.user_id, model.chat_id)
        can_ban = socket in self._active_chats.get(model.chat_id) and \
            admin and not server.services.chat_service.is_user_admin(model.banned_user_id, model.chat_id) \
            and server.services.user_service.does_user_exist(model.banned_user_id)

        if can_ban:
            chat = server.services.chat_service.get_chat(model.chat_id)
            if chat:
                self._ban_user(model.chat_id, model.banned_user_id, session.user_id)
            else:
                resp.action = message.Actions.RESPONSE
                resp_model = models.Response()
                resp_model.error = True
                resp_model.message = "Chat wasn't found"
                resp_model.error_code = message.ErrorCodes.CHAT_NOT_FOUND
                resp.arguments = resp_model
                resp.token = token
                self._try_send(socket, message.serialize(resp))
        else:
            resp.action = message.Actions.RESPONSE
            resp_model = models.Response()
            resp_model.error = True
            resp_model.message = "You don't have permissions to ban this user"
            resp_model.error_code = message.ErrorCodes.NOT_ENOUGH_PERMISSIONS
            resp.arguments = resp_model
            resp.token = token
            self._try_send(socket, message.serialize(resp))

    def _open_user_ban_vote(self, socket, model, token=""):
        """
        Opens user ban vote
        :param socket: socket of the users who want to ban other user
        :param model: ban model
        :param token: response token
        """
        resp = message.Message()
        session = self._connections.get_session(socket)

        can_ban = socket in self._active_chats.get(model.chat_id) \
            and not server.services.chat_service.is_user_admin(model.banned_user_id, model.chat_id)
        if can_ban:
            chat = server.services.chat_service.get_chat(model.chat_id)
            if chat:
                if self._active_chats.has_key(model.chat_id):
                    vote_key = (model.chat_id, model.banned_user_id)
                    self._active_ban_votes.open_vote(vote_key, self._config.vote_timer,
                                                     lambda r: (lambda c, u, r: self._close_vote(c, u, r))(
                                                         model.chat_id, model.banned_user_id, r))

                    # fill default votes for all users in chat
                    # default value is False, True is only for user, who suggest ban
                    sockets = self._active_chats.get(model.chat_id)
                    for s in sockets:
                        s_session = self._connections.get_session(s)
                        if session.user_id != model.banned_user_id:
                            self._active_ban_votes.vote(vote_key,
                                                        s_session.user_id,
                                                        s_session.user_id == session.user_id)

                resp.action = message.Actions.USER_BAN_VOTE_IS_OPENED
                resp_model = models.BanVote()
                resp_model.chat_id = model.chat_id
                resp_model.banned_user_id = model.banned_user_id
                resp_model.initiator_id = session.user_id
                resp_model.timeout = self._config.vote_timer
                resp.arguments = resp_model
                self._broadcast(model.chat_id, resp)
            else:
                resp.action = message.Actions.RESPONSE
                resp_model = models.Response()
                resp_model.error = True
                resp_model.message = "Chat wasn't found"
                resp_model.error_code = message.ErrorCodes.CHAT_NOT_FOUND
                resp.arguments = resp_model
                self._try_send(socket, message.serialize(resp))
        else:
            resp.action = message.Actions.RESPONSE
            resp_model = models.Response()
            resp_model.error = True
            resp_model.message = "You don't have permissions to ban this user"
            resp_model.error_code = message.ErrorCodes.NOT_ENOUGH_PERMISSIONS
            resp.arguments = resp_model
            resp.token = token
            self._try_send(socket, message.serialize(resp))

    def _vote_for_user_ban(self, socket, model, token=""):
        """
        Votes for user ban
        :param socket: socket of voter
        :param model: vote model. Type is models.UserChatPair
        :param token: response token
        """

        if socket in self._active_chats.get(model.chat_id, []):
            session = self._connections.get_session(socket)
            self._active_ban_votes.vote((model.chat_id, model.user_id), session.user_id, True, True)
            msg = message.Message()
            msg.action = message.Actions.VOTE_FOR_USER_BAN
            m = models.BanVote()
            m.chat_id = model.chat_id
            m.initiator_id = session.user_id
            m.banned_user_id = model.user_id
            msg.arguments = m
            self._broadcast(model.chat_id, msg)
        else:
            resp_model = models.Response()
            resp_model.error = True
            resp_model.error_code = message.ErrorCodes.NOT_ENOUGH_PERMISSIONS
            resp_model.message = "You aren't member of the chat"
            resp = message.Message()
            resp.action = message.Actions.RESPONSE
            resp.arguments = resp_model
            resp.token = token
            self._try_send(resp_model)

    def _remove_user_from_chat(self, socket, chat_id, token=""):
        """
        Removes user from chat. Called when user leaves chat
        :param socket: user's socket
        :param chat_id: Chat id
        :param token: response token
        """
        session = self._connections.get_session(socket)
        server_message = message.Message()
        server_message.action = message.Actions.USER_IS_OFFLINE
        user = models.User()
        user.user_id = session.user_id
        user.guest = session.is_guest
        user.login = session.login
        server_message.arguments = (chat_id, user)
        self._broadcast(chat_id, server_message, socket)
        self._remove_socket_from_room(chat_id, socket)

    def _make_admin(self, socket, model, token=""):
        """
        Makes user admin of the chat
        :param model: type is models.UserOfChat
        :param token: response token
        """
        session = self._connections.get_session(socket)
        if server.services.chat_service.is_user_admin(session.user_id, model.chat_id) and \
                not server.services.chat_service.is_user_admin(model.user_id, model.chat_id):
            server.services.chat_service.add_admin_to_chat(model.user_id, model.chat_id)
            server_message = message.Message()
            server_message.action = message.Actions.USER_WAS_MADE_ADMIN
            server_message.arguments = model
            self._broadcast(model.chat_id, server_message)
        else:
            resp_model = models.Response()
            resp_model.error = True
            resp_model.error_code = message.ErrorCodes.NOT_ENOUGH_PERMISSIONS
            resp_model.message = "You aren't admin of the chat or user is already admin"
            resp = message.Message()
            resp.action = message.Actions.RESPONSE
            resp.arguments = resp_model
            resp.token = token
            self._try_send(resp_model)

    def _close_vote(self, chat_id, banned_user_id, results):
        """
        Closes user ban vote and broadcast result of voting
        :rtype : object
        :param chat_id: chat id from where user was suggested to be kicked out
        :param banned_user_id: user id who was suggested to be kicked out
        :param results: dictionary of vote results: key is the voter id, value is the vote
        """
        is_banned = False
        if results and len([k for k, v in results.iteritems() if v]) / float(
                len([k for k, v in results.iteritems()])) > 0.5:
            self._ban_user(chat_id, banned_user_id)
            is_banned = True

        if not is_banned:
            model = models.UserChatPair()
            model.user_id = banned_user_id
            model.chat_id = chat_id
            msg = message.Message()
            msg.action = message.Actions.USER_BAN_VOTE_IS_CLOSED
            msg.arguments = model
            self._broadcast(chat_id, msg)

    def _ban_user(self, chat_id, banned_user_id, initiator_id=0):
        """
        Bans user
        :param chat_id: Chat id
        :param banned_user_id: Banned user id
        :param initiator_id: Id of the user who banned. 0 if ban is the result of vote
        """
        server.services.chat_service.ban_user(banned_user_id, chat_id)
        resp = message.Message()
        resp.action = message.Actions.USER_WAS_BANNED
        resp_model = models.Ban()
        resp_model.chat_id = chat_id
        resp_model.banned_user_id = banned_user_id
        resp_model.initiator_id = initiator_id
        resp.arguments = resp_model
        self._broadcast(chat_id, resp)
        self._remove_user_from_room(chat_id, banned_user_id)

    def _broadcast(self, chat_id, msg, sender=None):
        """
        Broadcast message to all members of the chat
        :param chat_id: Chat id
        :param msg: Message
        :param sender: Sender of the message. If sender is also member of the chat message won't be send to it again.
        """
        data = message.serialize(msg)
        room = self._active_chats.get(chat_id)
        for socket in room:
            if sender is None or socket != sender:
                self._try_send(socket, data)

    def _remove_user_from_room(self, room, user_id, resp=None):
        if user_id <= 0:
            return

        if not self._active_chats.has_key(room):
            return

        for s in self._connections.get_keys():
            if self._connections.get_session(s).user_id == user_id:
                if not resp is None:
                    self._try_send(s, message.serialize(resp))
                self._remove_socket_from_room(room, s)
                break

    def _remove_socket_from_room(self, room, sock):
        self._active_chats.remove(room, sock)

    def _try_send(self, socket, data):
        try:
            socket.send(data)
        except Exception as ex:
            self._logger.exception(ex)


class Session():
    def __init__(self):
        self.address = ''
        self.user_id = 0
        self.login = ''
        self.is_guest = True


class EmptyDataError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

    def __init__(self):
        Exception.__init__(self)


class Configuration():
    def __init__(self, file_name):
        self.__config = ConfigParser.RawConfigParser()
        self.__config.read(file_name)

    @property
    def _config(self):
        """
        RawConfigParser
        """
        return self.__config

    @property
    def buffer_size(self):
        """
        Buffer size in bytes
        """
        return self._config.getint('Socket', 'buffer')

    @property
    def host(self):
        """
        Server's host
        """
        return self._config.get('Socket', 'host')

    @property
    def port(self):
        """
        Server's port
        """
        return self._config.getint('Socket', 'port')

    @property
    def vote_timer(self):
        """
        Vote timer in seconds.
        """
        return self._config.getint('Chat', 'vote_timer')

