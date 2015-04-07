import PyQt4.QtCore
import PyQt4.QtGui


class ChatUserItem(PyQt4.QtGui.QWidget):
    """
    Widget for managing one of the users in the chat
    """
    @property
    def _user(self):
        return self.__user

    @property
    def _menu(self):
        return self.__menu

    def __init__(self, parent, user, menu=None):
        PyQt4.QtGui.QWidget.__init__(self, parent)
        self.__user = user
        self.__menu = menu

        self.layout = PyQt4.QtGui.QHBoxLayout(self)
        if user.guest:
            desc = "guest"
        elif user.admin:
            desc = "admin"
        else:
            desc = "registered"

        self.lbl_title = PyQt4.QtGui.QLabel("{0} ({1})".format(user.login, desc))
        self.lbl_title.contextMenuEvent = self.contextMenuEvent
        self.layout.addWidget(self.lbl_title)

    def contextMenuEvent(self, event):
        if not self._menu is None:
            self._menu.exec_(event.globalPos())

    # def addBanVote(self, action, timeout):
    #     self.vote_timeout = datetime.now() + datetime.timedelta(seconds=timeout)
    #     self.btn_vote = PyQt4.QtGui.QPushButton()
    #     self.btn_vote.clicked.connect(lambda: self._vote_for_ban(action))
    #     self.layout.addWidget(self.btn_vote, alignment=PyQt4.QtCore.Qt.AlignRight)
    #
    #     timer = PyQt4.QtCore.QTimer()
    #     timer.singleShot(self.vote_timeout * 1000, self._stop_vote)
    #
    #     # self.vote_ui_timer = PyQt4.QtCore.QTimer()
    #     # self.vote_ui_timer.start(1000)
    #     # self.vote_ui_timer.interval(lambda: self.btn_vote.setText("Vote for ban"))
    #
    # def _vote_for_ban(self, action):
    #     self._stop_vote()
    #     action()
    #
    # def _stop_vote(self):
    #     self.vote_ui_timer.stop()
    #     del self.btn_vote

    # def _update_vote_title(self):
