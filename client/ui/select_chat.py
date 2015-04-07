import PyQt4.QtCore
import PyQt4.QtGui
import PyQt4.Qt
import styles


class SelectChatWindow(PyQt4.QtGui.QDialog):

    _chat = None

    @property
    def chat(self):
        return self._chat

    @property
    def _service(self):
        return self.__service

    def __init__(self, service, guest, parent=None):
        super(SelectChatWindow, self).__init__(parent)

        self.__service = service

        self.setWindowTitle("Select chat")

        palette = PyQt4.QtGui.QPalette()
        palette.setColor(PyQt4.QtGui.QPalette.Foreground, PyQt4.QtCore.Qt.red)
        self.lbl_error_message = PyQt4.QtGui.QLabel("", self)
        self.lbl_error_message.setPalette(palette)

        self.lw_chats_list = PyQt4.QtGui.QListWidget(self)
        self.lw_chats_list.setFrameStyle(PyQt4.QtGui.QFrame.Box | PyQt4.QtGui.QFrame.Plain)

        self.lb_password = PyQt4.QtGui.QLabel("Chat password")

        self.le_password = PyQt4.QtGui.QLineEdit()
        self.le_password.setEchoMode(PyQt4.QtGui.QLineEdit.Password)
        self.le_password.setDisabled(True)

        # Button to select chat
        self.btn_select = PyQt4.QtGui.QPushButton('Ok', self)
        self.btn_select.clicked.connect(self.select_chat)
        self.btn_select.setDisabled(True)

        layout = PyQt4.QtGui.QGridLayout(self)
        layout.setSpacing(10)
        layout.addWidget(self.lbl_error_message, 0, 0, 1, 2)
        layout.addWidget(self.lw_chats_list, 1, 0, 1, 2)
        layout.addWidget(self.lb_password, 2, 0)
        layout.addWidget(self.le_password, 2, 1)
        layout.addWidget(self.btn_select, 3, 1)

        # Load chats
        try:
            self._service.load_chats(self.load_chats_callback)
        except:
            self.parent().handle_server_error()

        self.lw_chats_list.itemSelectionChanged.connect(self._chat_selection_changed)

    def _add_chat(self, user_chat):
        item = PyQt4.QtGui.QListWidgetItem()
        # item.setSizeHint(PyQt4.QtCore.QSize(10, 30))

        title = user_chat.name
        descriptions = []
        if user_chat.admin:
            descriptions.append('admin')
        if user_chat.private:
            descriptions.append('private')
        if user_chat.opened:
            descriptions.append('opened')
        else:
            descriptions.append('authorized')

        title += ': ' + ', '.join(descriptions)
        item.setText(title)
        item.setData(PyQt4.QtCore.Qt.UserRole, user_chat)
        self.lw_chats_list.addItem(item)

    def select_chat(self):
        self._chat = self._get_selected_chat()
        if self._chat.private:
            password = str(self.le_password.text())
        else:
            password = ""
        try:
            self._service.enter_chat(self._chat.chat_id, password, self.enter_room_callback)
        except:
            self.parent().handle_server_error()

    def load_chats_callback(self, chats_list_response):
        if chats_list_response:
            for c in chats_list_response:
                self._add_chat(c)
            self.lw_chats_list.setItemDelegate(styles.ListItemDelegate(self))
            self.lw_chats_list.setFrameStyle(PyQt4.QtGui.QFrame.Box | PyQt4.QtGui.QFrame.Plain)

    def enter_room_callback(self, chats_response):
        if not chats_response.error:
            self._chat = chats_response
            self.accept()
        else:
            self.lbl_error_message.setText(chats_response.message)

    def _chat_selection_changed(self):
        chat = self._get_selected_chat()
        self.le_password.setDisabled(not chat.private)
        self.btn_select.setDisabled(chat is None)

    def _get_selected_chat(self):
        item = self.lw_chats_list.currentItem()
        if not item:
            return
        chat = item.data(PyQt4.QtCore.Qt.UserRole).toPyObject()
        return chat