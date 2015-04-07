import PyQt4.QtCore
import PyQt4.QtGui


def ServerIsUnavailable(parent):
    return PyQt4.QtGui.QMessageBox.critical(parent, 'Error', 'Server is unavailable.',
                                            PyQt4.QtGui.QMessageBox.Abort | PyQt4.QtGui.QMessageBox.Ignore)


def InternalServerError(parent):
    return PyQt4.QtGui.QMessageBox.critical(parent, 'Error', 'Internal server error.', PyQt4.QtGui.QMessageBox.Ok)


def ConnectionIsFailed(parent):
    return PyQt4.QtGui.QMessageBox.critical(parent, 'Error', 'Connection to the server is failed.',
                                            PyQt4.QtGui.QMessageBox.Ok)
