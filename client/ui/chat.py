
import PyQt4.QtCore
import PyQt4.QtGui
import new_chat
import os
import select_chat
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(here, '../../utilities')))
from utilities import message

import error_message
import styles
from widgets.chat_title_item import ChatTitleItem
from widgets.chat_messages_item import ChatMessagesItem


class ChatWindow(PyQt4.QtGui.QMainWindow):

    @property
    def _chats(self):
        """
        Dictionary of chats. Key is Chat_id. Value is (utilities.models.UserMessage, ChatTitleItem, ChatMessagesItem)
        """
        return self.__chats

    @property
    def _service(self):
        """
        Service that manages user's actions and send requests to server
        """
        return self.__service

    @property
    def _user(self):
        """
        User data
        """
        return self.__user

    def __init__(self, service, user, parent=None):

        super(ChatWindow, self).__init__(parent)

        self.__chats = {}
        self.__service = service
        self.__user = user

        self.setWindowTitle("Chats - {0}".format(self._user.login))

        splitter = PyQt4.QtGui.QSplitter()
        self.setCentralWidget(splitter)

        self.lw_chats_list = PyQt4.QtGui.QListWidget(self)
        self.lw_chats_list.setFrameStyle(PyQt4.QtGui.QFrame.Box | PyQt4.QtGui.QFrame.Plain)
        self.lw_chats_list.itemSelectionChanged.connect(self.chat_selection_changed)

        splitter.addWidget(self.lw_chats_list)

        self.sw_messages_list = PyQt4.QtGui.QStackedWidget()
        self.sw_messages_list.setFrameStyle(PyQt4.QtGui.QFrame.Box | PyQt4.QtGui.QFrame.Plain)
        splitter.addWidget(self.sw_messages_list)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.lw_chats_list.setItemDelegate(styles.ListItemDelegate(self))

        self._set_menu()

    def _set_menu(self):
        self.main_menu = self.menuBar()
        self.chat_menu = self.main_menu.addMenu("Chats")

        find_chat_action = PyQt4.QtGui.QAction('&Select chat', self)
        find_chat_action.triggered.connect(self.find_chat_window)
        self.chat_menu.addAction(find_chat_action)

        new_chat_action = PyQt4.QtGui.QAction('&New chat', self)
        self.chat_menu.addAction(new_chat_action)
        # self.connect(new_chat_action, PyQt4.QtCore.SIGNAL('triggered()'), self, PyQt4.QtCore.SLOT('new_chat_window()'))
        new_chat_action.triggered.connect(self.new_chat_window)

    def _add_chat(self, user_chat):
        if user_chat.chat_id in self._chats.keys():
            return

        item = PyQt4.QtGui.QListWidgetItem()
        item.setSizeHint(PyQt4.QtCore.QSize(10, 35))
        chat_title_item = ChatTitleItem(self, user_chat)
        chat_messages_item = ChatMessagesItem(self, self._service, self._user, user_chat)
        chat_messages_item.te_message.focusInEvent = lambda e: chat_title_item.clear_notification()
        chat_messages_item.te_messages.focusInEvent = lambda e: chat_title_item.clear_notification()

        self._chats[user_chat.chat_id] = ChatItem(user_chat, chat_title_item, chat_messages_item)

        self.lw_chats_list.addItem(item)
        self.lw_chats_list.setItemWidget(item, chat_title_item)
        self.sw_messages_list.addWidget(chat_messages_item)
        self.lw_chats_list.setCurrentRow(self.lw_chats_list.count() - 1)

    def chat_selection_changed(self):
        selected_item = self.lw_chats_list.currentItem()
        if selected_item:
            widget = self.lw_chats_list.itemWidget(selected_item)
            chat_item = self._chats[widget.chat.chat_id]
            self.sw_messages_list.setCurrentWidget(chat_item.messages)
            widget.clear_notification()

    def server_message(self, response):
        if response.error:
            self.handle_server_error(response.error_code)

    def handle_server_error(self, error_code):
        reply = None
        if error_code == message.ErrorCodes.SERVER_IS_UNAVAILABLE:
            reply = error_message.ServerIsUnavailable(self)
        elif error_code == message.ErrorCodes.INTERNAL_SERVER_ERROR:
            reply = error_message.InternalServerError(self)
        if reply == PyQt4.QtGui.QMessageBox.Abort:
            self.close()


    def user_message(self, user_message):
        """
        Messages from other users
        :param user_message: utilities.models.UserMessage
        """

        if not user_message.chat_id in self._chats.keys():
            return
        chat_item = self._chats[user_message.chat_id]
        chat_item.messages.receive_message(user_message)

        selected_item = self.lw_chats_list.currentItem()
        if selected_item:
            widget = self.lw_chats_list.itemWidget(selected_item)
            active_chat_item = self._chats[widget.chat.chat_id]
            if active_chat_item.title != chat_item.title or not chat_item.messages.hasFocus():
                chat_item.title.notification()

    def add_user(self, chat_id, user):
        if not chat_id in self._chats.keys():
            return
        chat_item = self._chats[chat_id]
        chat_item.messages.add_user(user)

    def remove_user(self, chat_id, user):
        if not chat_id in self._chats.keys():
            return
        chat_item = self._chats[chat_id]
        chat_item.messages.remove_user(user)

    def remove_banned_user(self, ban):
        if not ban.chat_id in self._chats.keys():
            return
        chat_item = self._chats[ban.chat_id]
        if ban.banned_user_id == self._user.user_id:
            self._remove_chat(ban.chat_id)
            PyQt4.QtGui.QMessageBox.information(
                None, 'Ban', "You was banned in the chat '{0}'".format(chat_item.user_chat.name))
        else:
            chat_item.messages.remove_banned_user(ban.banned_user_id)

    def update_user_as_admin(self, user_chat_pair):
        if not user_chat_pair.chat_id in self._chats.keys():
            return

        chat_item = self._chats[user_chat_pair.chat_id]
        chat_item.messages.update_user_as_admin(user_chat_pair.user_id)

    def add_user_ban_vote(self, ban_vote):
        if not ban_vote.chat_id in self._chats.keys():
            return
        chat_item = self._chats[ban_vote.chat_id]
        chat_item.messages.add_ban_vote(ban_vote)

    def close_user_ban_vote(self, user_chat_pair):
        if not user_chat_pair.chat_id in self._chats.keys():
            return
        chat_item = self._chats[user_chat_pair.chat_id]
        chat_item.messages.close_user_ban_vote(user_chat_pair.user_id)

    def update_user_ban_vote(self, ban_vote):
        chat_item = self._chats[ban_vote.chat_id]
        chat_item.messages.update_user_ban_vote(ban_vote)

    def leave_chat(self, chat_id):
        self._remove_chat(chat_id)
        try:
            self._service.leave_chat(chat_id)
        except:
            self.handle_server_error()

    def new_chat_window(self):
        window = new_chat.NewChatWindow(self._service, self._user.guest, self)
        window.accepted.connect(self.chat_authorize)
        window.show()

    def find_chat_window(self):
        window = select_chat.SelectChatWindow(self._service, self._user.guest, self)
        # self.connect(window, PyQt4.QtCore.SIGNAL('accepted()'), self, PyQt4.QtCore.SLOT('chat_authorize()'))
        window.accepted.connect(self.chat_authorize)
        window.show()

    def chat_authorize(self):
        sender = self.sender()
        self._add_chat(sender.chat)

    def _remove_chat(self, chat_id):
        chat_item = self._chats[chat_id]
        del self._chats[chat_id]
        for i in xrange(self.lw_chats_list.count()):
            item = self.lw_chats_list.item(i)
            if self.lw_chats_list.itemWidget(item) == chat_item.title:
                self.lw_chats_list.takeItem(i)
                break
        self.sw_messages_list.removeWidget(chat_item.messages)


class ChatItem:

    @property
    def user_chat(self):
        """
        Data about chat and current user role in this chat
        Type is utilities.models.ChatResponse
        """
        return self.__user_chat

    @property
    def title(self):
        """
        Title widget
        Type is widgets.chat_title_item
        """
        return self.__title

    @property
    def messages(self):
        """
        Messages widget
        Type is widgets.chat_messages_item
        """
        return self.__messages

    def __init__(self, user_chat, title, messages):
        self.__user_chat = user_chat
        self.__title = title
        self.__messages = messages

