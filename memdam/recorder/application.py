
import sys
import concurrent.futures
import Queue

from PyQt4 import QtCore, QtGui

import memdam
import memdam.common.error

_QAPP = None

def app():
    global _QAPP
    if _QAPP == None:
        _QAPP = MyQApp(sys.argv[:1])
    return _QAPP

class MyQApp(QtGui.QApplication):
    
    def __init__(self, *args, **kwargs):
        QtGui.QApplication.__init__(self, *args, **kwargs)
        self._task_queue = Queue.Queue()
    
    def process_external_commands(self):
        """
        This will run functions from the main loop and fulfill your futures.
        """
        try:
            #memdam.log.info("Processing commands")
            data = self._task_queue.get_nowait()
            if data != None:
                func, future = data
                try:
                    if future.set_running_or_notify_cancel():
                        future.set_result(func())
                except Exception, e:
                    future.set_exception(e)
        except Queue.Empty:
            pass
        except Exception, e:
            memdam.common.error.report(e)
        finally:
            QtCore.QTimer.singleShot(0, self.process_external_commands)

    def add_task(self, func):
        future = concurrent.futures.Future()
        self._task_queue.put((func, future))
        return future

#Based off of this:  http://ftp.ics.uci.edu/pub/centos0/ics-custom-build/BUILD/PyQt-x11-gpl-4.7.2/examples/desktop/systray/systray.py
class Window(QtGui.QDialog):
    def __init__(self, shutdown_func):
        super(Window, self).__init__()

        self._shutdown_func = shutdown_func
        self.createActions()
        self.createTrayIcon()
        
        self.icon = QtGui.QIcon('heart.svg')
        self.trayIcon.setIcon(self.icon)
        self.setWindowIcon(self.icon)

        self.trayIcon.show()

        self.setWindowTitle("Systray")
        self.resize(400, 300)


    def setVisible(self, visible):
        self.minimizeAction.setEnabled(visible)
        self.maximizeAction.setEnabled(not self.isMaximized())
        self.restoreAction.setEnabled(self.isMaximized() or not visible)
        super(Window, self).setVisible(visible)

    def closeEvent(self, event):
        if self.trayIcon.isVisible():
            QtGui.QMessageBox.information(self, "Systray",
                    "The program will keep running in the system tray. To "
                    "terminate the program, choose <b>Quit</b> in the "
                    "context menu of the system tray entry.")
            self.hide()
            event.ignore()
            
    def doQuit(self, *args, **kwargs):
        self._shutdown_func()
        QtGui.qApp.quit()

    def createActions(self):
        self.minimizeAction = QtGui.QAction("Mi&nimize", self,
                triggered=self.hide)

        self.maximizeAction = QtGui.QAction("Ma&ximize", self,
                triggered=self.showMaximized)

        self.restoreAction = QtGui.QAction("&Restore", self,
                triggered=self.showNormal)

        self.quitAction = QtGui.QAction("&Quit", self,
                triggered=self.doQuit)

    def createTrayIcon(self):
         self.trayIconMenu = QtGui.QMenu(self)
         self.trayIconMenu.addAction(self.minimizeAction)
         self.trayIconMenu.addAction(self.maximizeAction)
         self.trayIconMenu.addAction(self.restoreAction)
         self.trayIconMenu.addSeparator()
         self.trayIconMenu.addAction(self.quitAction)

         self.trayIcon = QtGui.QSystemTrayIcon(self)
         self.trayIcon.setContextMenu(self.trayIconMenu)

    