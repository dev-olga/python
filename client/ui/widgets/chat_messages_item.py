import sys
import os

from datetime import datetime

import PyQt4.QtCore
import PyQt4.QtGui

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(here, '../../ui')))

from ui import error_message
from ui import styles

from chat_user_item import ChatUserItem


class ChatMessagesItem(PyQt4.QtGui.QWidget):
    """
    Widget for sending messages and users management
    """

    @property
    def chat(self):
        return self.__chat

    @property
    def _service(self):
        return self.__service

    @property
    def _user(self):
        return self.__user

    @property
    def _parent(self):
        return self.__parent

    def __init__(self, parent, service, user, chat_response):
        PyQt4.QtGui.QWidget.__init__(self, parent)

        self.__parent = parent
        self.__service = service
        self.__user = user
        self.__chat = chat_response

        # Users
        self.lw_users = PyQt4.QtGui.QListWidget(self)
        self.lw_users.setItemDelegate(styles.ListItemDelegate(self))
        self._render_users()

        # Chat messages
        self.te_messages = PyQt4.QtGui.QTextEdit(self)
        self.te_messages.setReadOnly(True)

        # User's message
        self.te_message = PyQt4.QtGui.QTextEdit(self)

        self.btn_send = PyQt4.QtGui.QPushButton('Send', self)
        self.btn_send.clicked.connect(self.send_message)
        self.btn_send.setFixedHeight(20)
        self.btn_send.setFixedWidth(styles.BUTTON_DEFAULT_WIDTH)

        main_layout = PyQt4.QtGui.QHBoxLayout(self)
        bottom = PyQt4.QtGui.QWidget(self)
        bottom.setMinimumSize(100, 100)
        bottom_layout = PyQt4.QtGui.QGridLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addWidget(self.te_message, 0, 0, 1, 2)
        bottom_layout.addWidget(self.btn_send, 1, 1)
        bottom.setLayout(bottom_layout)

        splitter1 = PyQt4.QtGui.QSplitter(PyQt4.QtCore.Qt.Vertical)
        splitter1.addWidget(self.lw_users)
        splitter1.addWidget(self.te_messages)
        splitter1.setStretchFactor(0, 0)
        splitter1.setStretchFactor(1, 1)
        splitter1.setHandleWidth(10)
        splitter1.setSizes([1, 2])

        splitter2 = PyQt4.QtGui.QSplitter(PyQt4.QtCore.Qt.Vertical)
        splitter2.addWidget(splitter1)
        splitter2.addWidget(bottom)
        splitter2.setCollapsible(1, False)
        splitter2.setCollapsible(0, False)
        splitter2.setStretchFactor(0, 1)
        splitter2.setStretchFactor(1, 0)
        splitter2.setHandleWidth(10)
        splitter2.setSizes([1, 2])

        main_layout.addWidget(splitter2)
        self.setLayout(main_layout)

    def send_message(self):
        message = str(self.te_message.toPlainText())
        if message.strip():
            self.te_message.clear()
            self._render_message("Red", "{0}:".format(self._user.login))
            self.te_messages.insertHtml("<br>" + message)
            self._move_cursor_to_end()

            try:
                self._service.send_message(self.chat.chat_id, message)
            except:
                self._parent.handle_server_error()

    def receive_message(self, user_message):
        if user_message.guest:
            desc = "guest"
        else:
            user = [u for u in self.chat.users if u.user_id == user_message.user_id and u.admin][:1]
            if len(user) > 0:
                desc = "admin"
            else:
                desc = "registered"
        self._render_message("Blue", "{0} ({1}):".format(user_message.login, desc))
        self.te_messages.insertHtml("<br>" + str(user_message.message))
        self._move_cursor_to_end()

    def remove_user(self, user):
        for u in self.chat.users:
            if u.user_id == user.user_id or (u.guest and user.guest and u.login == user.login):
                self.chat.users.remove(u)
                break

        self._render_message("Grey", "{0} is offline.".format(user.login))
        self._render_users()

    def remove_banned_user(self, user_id):
        user = None
        for u in self.chat.users:
            if u.user_id == user_id:
                user = u
                self.chat.users.remove(u)
                break
        if user:
            self._render_message("Grey", "{0} was banned.".format(user.login))
        self._render_users()

    def add_user(self, user):
        self.chat.users.append(user)
        self._render_message("Grey", "{0} joined the chat.".format(user.login))
        self._render_users()

    def update_user_as_admin(self, user_id):
        if self._user.user_id == user_id:
            self.chat.admin = True
            self._render_message("Grey", "{0} was made an admin.".format(self._user.login))
        else:
            try:
                user = (u for u in self.chat.users if u.user_id == user_id).next()
                user.admin = True
                self._render_message("Grey", "{0} was made an admin.".format(user.login))
            except StopIteration:
                pass
        self._render_users()

    def add_ban_vote(self, ban):
        banned_user = [u for u in self.chat.users if u.user_id == ban.banned_user_id][:1]
        if banned_user:
            banned_user = banned_user[0]
        elif ban.banned_user_id == self._user.user_id:
            banned_user = self._user

        initiator = [u for u in self.chat.users if u.user_id == ban.initiator_id][:1]
        if initiator:
            initiator = initiator[0]
        elif ban.initiator_id == self._user.user_id:
            initiator = self._user

        if banned_user and initiator:
            self._render_message("Grey", "{0} suggested to kick {1}.".format(initiator.login, banned_user.login))
            for u in self.chat.users:
                if u.user_id == ban.banned_user_id:
                    u.is_in_ban_vote = True
                    u.can_be_voted = initiator != self._user

            self._render_users()

    def close_user_ban_vote(self, user_id):
        banned_user = [u for u in self.chat.users if u.user_id == user_id][:1]
        if banned_user:
            banned_user = banned_user[0]
        elif user_id == self._user.user_id:
            banned_user = self._user

        if banned_user:
            self._render_message("Grey", "Kick vote for {0} is closed.".format(banned_user.login))
            for u in self.chat.users:
                if u.user_id == user_id:
                    u.is_in_ban_vote = False
                    u.can_be_voted = True
            self._render_users()

    def update_user_ban_vote(self, ban):
        banned_user = [u for u in self.chat.users if u.user_id == ban.banned_user_id][:1]
        if banned_user:
            banned_user = banned_user[0]
        elif ban.banned_user_id == self._user.user_id:
            banned_user = self._user

        initiator = [u for u in self.chat.users if u.user_id == ban.initiator_id][:1]
        if initiator:
            initiator = initiator[0]
        elif ban.initiator_id == self._user.user_id:
            initiator = self._user

        if banned_user and initiator:
            self._render_message("Grey", "{0} voted for {1} kicking.".format(initiator.login, banned_user.login))

    def _vote_for_ban(self, user):
        user.can_be_voted = False
        self._render_users()
        self._service.vote_for_ban(self.chat.chat_id, user.user_id)

    def _render_message(self, color, message):
        self._move_cursor_to_end()
        text = "<font color=\"{0}\">{1:%Y-%m-%d %H:%M:%S}: {2}</font>".format(color, datetime.now(), message)
        if self.te_messages.toPlainText() != "":
            text = "<br>" + text
        self.te_messages.insertHtml(text)
        self._move_cursor_to_end()

    def _move_cursor_to_end(self):
        cursor = self.te_messages.textCursor()
        cursor.movePosition(PyQt4.QtGui.QTextCursor.End)
        self.te_messages.setTextCursor(cursor)

    def _render_users(self):
        self.lw_users.clear()
        i = 0
        for u in sorted(self.chat.users, key=lambda user: user.login):
            item = PyQt4.QtGui.QListWidgetItem()
            item.setSizeHint(PyQt4.QtCore.QSize(10, 30))
            self.lw_users.addItem(item)
            popMenu = None
            if not self.chat.opened and not u.admin:
                popMenu = PyQt4.QtGui.QMenu(self)
                add_admin_action = None
                user_id = u.user_id
                kick_action = PyQt4.QtGui.QAction('Kick', self)
                if self.chat.admin:
                    kick_action.triggered.connect((lambda id: lambda: self._kick_user(id))(user_id))
                    add_admin_action = PyQt4.QtGui.QAction('Make admin', self)
                    add_admin_action.triggered.connect((lambda id: lambda: self._make_admin(id))(user_id))

                elif u.is_in_ban_vote:
                    kick_action.triggered.connect(
                        (lambda user:
                         lambda: (self._vote_for_ban(user), kick_action.setDisabled(True)))(u))
                    if not u.can_be_voted:
                        kick_action.setDisabled(True)
                else:
                    kick_action.triggered.connect((lambda id: lambda: self._create_ban_vote(id))(user_id))
                popMenu.addAction(kick_action)
                if add_admin_action:
                    popMenu.addAction(add_admin_action)
            w = ChatUserItem(self, u, popMenu)
            self.lw_users.setItemWidget(item, w)

    def _kick_user(self, user_id):
        try:
            self._service.ban_user(self.chat.chat_id, user_id)
        except:
            self._parent.handle_server_error()

    def _create_ban_vote(self, user_id):
        try:
            self._service.create_ban_vote(self.chat.chat_id, user_id)
        except:
            self._parent.handle_server_error()

    def _make_admin(self, user_id):
        try:
            self._service.make_admin(self.chat.chat_id, user_id)
        except:
            self._parent.handle_server_error()