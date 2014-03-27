
import sys

import PyQt4.QtCore
import PyQt4.QtGui

import memdam.common.utils
import memdam.recorder.user.api
import memdam.recorder.application

class User(memdam.recorder.user.api.User):

    def __init__(self, ):
        self.app = memdam.recorder.application.app()

    def prompt_user(self, prompt_text):
        inputter = InputDialog(None, title="Please answer", label=prompt_text, text="")
        inputter.exec_()
        comment = inputter.text.text()
        return unicode(comment)

    def main_loop(self, start, shutdown):
        #launch as a qt app
        PyQt4.QtCore.QTimer.singleShot(0, self.app.process_external_commands)
        PyQt4.QtCore.QTimer.singleShot(1000, start)

        if not PyQt4.QtGui.QSystemTrayIcon.isSystemTrayAvailable():
            PyQt4.QtGui.QMessageBox.critical(None, "Systray",
                    "I couldn't detect any system tray on this system.")
            sys.exit(1)

        PyQt4.QtGui.QApplication.setQuitOnLastWindowClosed(False)
        return self.app.create_window_and_run(shutdown)

class InputDialog(PyQt4.QtGui.QDialog):
    '''
    this is for when you need to get some user input text
    '''
    def __init__(self, parent=None, title='user input', label='comment', text=''):

        PyQt4.QtGui.QWidget.__init__(self, parent)

        #--Layout Stuff---------------------------#
        mainLayout = PyQt4.QtGui.QVBoxLayout()

        layout = PyQt4.QtGui.QHBoxLayout()
        self.label = PyQt4.QtGui.QLabel()
        self.label.setText(label)
        layout.addWidget(self.label)

        self.text = PyQt4.QtGui.QLineEdit(text)
        layout.addWidget(self.text)

        mainLayout.addLayout(layout)

        #--The Button------------------------------#
        layout = PyQt4.QtGui.QHBoxLayout()
        button = PyQt4.QtGui.QPushButton("okay") #string or icon
        self.connect(button, PyQt4.QtCore.SIGNAL("clicked()"), self.close)
        layout.addWidget(button)

        mainLayout.addLayout(layout)
        self.setLayout(mainLayout)

        self.resize(400, 60)
