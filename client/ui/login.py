import PyQt4.QtCore
import PyQt4.QtGui

import error_message
import styles


class LoginWindow(PyQt4.QtGui.QDialog):

    @property
    def _service(self):
        return self.__service

    def __init__(self, service):
        self.__service = service

        PyQt4.QtGui.QDialog.__init__(self)

        self.setWindowTitle("Authorization")

        palette = PyQt4.QtGui.QPalette()
        palette.setColor(PyQt4.QtGui.QPalette.Foreground, PyQt4.QtCore.Qt.red)
        self.lbl_error_message = PyQt4.QtGui.QLabel("", self)
        self.lbl_error_message.setPalette(palette)
        self.lbl_error_message.setWordWrap(True)
        self.lbl_error_message.setMinimumHeight(30)
        self.lbl_error_message.hide()

        self.cb_is_guest = PyQt4.QtGui.QCheckBox("Guest", self)
        self.cb_is_guest.stateChanged.connect(self._is_guest_changed)
        self.le_name = PyQt4.QtGui.QLineEdit(self)
        self.le_password = PyQt4.QtGui.QLineEdit(self)
        self.le_password.setEchoMode(PyQt4.QtGui.QLineEdit.Password)
        self.lbl_name = PyQt4.QtGui.QLabel('Name', self)
        self.lbl_password = PyQt4.QtGui.QLabel('Password', self)

        self.btn_login = PyQt4.QtGui.QPushButton('Login', self)
        self.btn_login.clicked.connect(self._authorize)
        self.btn_login.setMinimumWidth(styles.BUTTON_DEFAULT_WIDTH)

        self.btn_register = PyQt4.QtGui.QPushButton('Register', self)
        self.btn_register.clicked.connect(self._register)
        self.btn_register.setMinimumWidth(styles.BUTTON_DEFAULT_WIDTH)

        layout = PyQt4.QtGui.QGridLayout(self)
        layout.setSpacing(10)
        layout.addWidget(self.lbl_error_message, 0, 0, 1, 3)
        layout.addWidget(self.lbl_name, 1, 0)
        layout.addWidget(self.le_name, 1, 1, 1, 2)
        layout.addWidget(self.lbl_password, 2, 0)
        layout.addWidget(self.le_password, 2, 1, 1, 2)
        layout.addWidget(self.cb_is_guest, 3, 0, 1, 2)
        layout.addWidget(self.btn_login, 4, 1, PyQt4.QtCore.Qt.AlignRight)
        layout.addWidget(self.btn_register, 4, 2, PyQt4.QtCore.Qt.AlignRight)

        self.setFixedWidth(250)

    def _authorize(self):
        try:
            self.setDisabled(True)
            self._service.authorize(
                str(self.le_name.text()), str(self.le_password.text()), self.cb_is_guest.isChecked(), self._callback)
        except:
            reply = error_message.ServerIsUnavailable()
            if reply == PyQt4.QtGui.QMessageBox.Abort:
                self.close()
            self.setDisabled(False)

    def _register(self):
        try:
            self.setDisabled(True)
            self._service.register(str(self.le_name.text()), str(self.le_password.text()), self._callback)
        except:
            reply = error_message.ServerIsUnavailable()
            if reply == PyQt4.QtGui.QMessageBox.Abort:
                self.close()
            self.setDisabled(False)

    def _callback(self, resp):
        if not resp.error:
            self.user = resp
            self.accept()
        else:
            self.lbl_error_message.setText(resp.message)
            self.lbl_error_message.show()
            self.setDisabled(False)

    def _is_guest_changed(self, i):
        self.le_password.setDisabled(self.cb_is_guest.isChecked())
        self.btn_register.setDisabled(self.cb_is_guest.isChecked())
