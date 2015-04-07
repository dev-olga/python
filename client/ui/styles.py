import PyQt4.QtCore
import PyQt4.QtGui


class ListItemDelegate(PyQt4.QtGui.QItemDelegate):
    def __init__(self, parent=None, *args):
        PyQt4.QtGui.QItemDelegate.__init__(self, parent, *args)

    def paint(self, painter, option, index):
        painter.save()

        # set background color
        painter.setPen(PyQt4.QtGui.QPen(PyQt4.QtCore.Qt.NoPen))
        if option.state & PyQt4.QtGui.QStyle.State_Selected:
            painter.setBrush(PyQt4.QtGui.QBrush(PyQt4.QtCore.Qt.gray))
        else:
            painter.setBrush(PyQt4.QtGui.QBrush(PyQt4.QtCore.Qt.white))
        painter.drawRect(option.rect)

        # set text color
        painter.setPen(PyQt4.QtGui.QPen(PyQt4.QtCore.Qt.black))
        value = index.data(PyQt4.QtCore.Qt.DisplayRole)
        if value.isValid():
            text = value.toString()
            painter.drawText(option.rect, PyQt4.QtCore.Qt.AlignLeft, text)

        painter.restore()


BUTTON_DEFAULT_WIDTH = 60
