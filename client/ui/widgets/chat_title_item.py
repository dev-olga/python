import PyQt4.QtCore
import PyQt4.QtGui
import os

class ChatTitleItem(PyQt4.QtGui.QWidget):
    """
    Widget for chat title and notifications
    """

    @property
    def chat(self):
        return self.__chat

    def __init__(self, parent, chat):
        PyQt4.QtGui.QWidget.__init__(self, parent)
        self.__chat = chat
        self.parent = parent

        layout = PyQt4.QtGui.QHBoxLayout(self)
        self.lbl_title = PyQt4.QtGui.QLabel(chat.name)
        self.lbl_title.setFixedHeight(15)

        self.lbl_notification = PyQt4.QtGui.QLabel('')
        palette = PyQt4.QtGui.QPalette()
        palette.setColor(PyQt4.QtGui.QPalette.Foreground, PyQt4.QtCore.Qt.red)
        self.lbl_notification.setPalette(palette)
        self.lbl_notification.setFixedWidth(20)

        self.btn_close = PyQt4.QtGui.QPushButton("x", self)
        self.btn_close.setToolTip("Close")
        self.btn_close.setFixedWidth(15)
        self.btn_close.setFixedHeight(15)
        self.btn_close.setToolTip("Close chat")
        self.btn_close.clicked.connect(lambda: self.parent.leave_chat(self.chat.chat_id))

        layout.addWidget(self.lbl_notification)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.btn_close, alignment=PyQt4.QtCore.Qt.AlignRight)

    def notification(self):
        pixmap = PyQt4.QtGui.QPixmap(os.path.dirname(os.path.abspath(__file__)) + "/new_msg.png")
        self.lbl_notification.setScaledContents(True)
        self.lbl_notification.setPixmap(pixmap)

    def clear_notification(self):
        self.lbl_notification.clear()