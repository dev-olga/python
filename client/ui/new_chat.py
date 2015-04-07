import PyQt4.QtCore
import PyQt4.QtGui


class NewChatWindow(PyQt4.QtGui.QDialog):

    _chat = None

    @property
    def chat(self):
        return self._chat

    @property
    def _service(self):
        return self.__service

    def __init__(self, service, guest, parent=None):
        super(NewChatWindow, self).__init__(parent)

        self.__service = service

        self.setWindowTitle("New chats")

        palette = PyQt4.QtGui.QPalette()
        palette.setColor(PyQt4.QtGui.QPalette.Foreground, PyQt4.QtCore.Qt.red)
        self.lbl_error_message = PyQt4.QtGui.QLabel("", self)
        self.lbl_error_message.setPalette(palette)

        self.le_name = PyQt4.QtGui.QLineEdit(self)
        self.lbl_name = PyQt4.QtGui.QLabel('Chat name', self)

        self.cb_is_private = PyQt4.QtGui.QCheckBox("Private", self)

        self.cb_is_private.stateChanged.connect(self.is_private_state_changed)
        self.lbl_password = PyQt4.QtGui.QLabel('Chat password', self)
        self.le_password = PyQt4.QtGui.QLineEdit(self)
        self.le_password.setDisabled(True)
        self.le_password.setEchoMode(PyQt4.QtGui.QLineEdit.Password)
        self.cb_is_opened = PyQt4.QtGui.QCheckBox("Opened", self)

        self.btn_create = PyQt4.QtGui.QPushButton('Create', self)
        self.btn_create.clicked.connect(self._create_chat)

        layout = PyQt4.QtGui.QGridLayout(self)
        layout.setSpacing(10)
        layout.addWidget(self.lbl_error_message, 0, 0, 1, 2)
        layout.addWidget(self.lbl_name, 1, 0)
        layout.addWidget(self.le_name, 1, 1)
        layout.addWidget(self.cb_is_opened, 2, 0, 1, 2)
        layout.addWidget(self.cb_is_private, 3, 0, 1, 2)
        layout.addWidget(self.lbl_password, 4, 0)
        layout.addWidget(self.le_password, 4, 1)
        layout.addWidget(self.btn_create, 5, 1)

        if guest:
            self.cb_is_opened.hide()
            self.cb_is_opened.setChecked(True)

    def is_private_state_changed(self, i):
        self.le_password.setDisabled(not self.cb_is_private.isChecked())

    def _create_chat(self):
        try:
            self._service.create_chat(str(self.le_name.text()), self.cb_is_opened.isChecked(),
                                      self.cb_is_private.isChecked(), str(self.le_password.text()),
                                      self._create_chat_callback)
        except:
            self.parent().handle_server_error()

    def _create_chat_callback(self, new_chat_response):
        if not new_chat_response.error:
            self._chat = new_chat_response
            if self._chat.private:
                password = str(self.le_password.text())
            else:
                password = ""
            try:
                self._service.enter_chat( self._chat.chat_id, password, self._enter_chat_callback)
            except:
                self.parent().handle_server_error()
        else:
            self.lbl_error_message.setText(new_chat_response.message)

    def _enter_chat_callback(self, chat):
        self._chat = chat
        self.accept()