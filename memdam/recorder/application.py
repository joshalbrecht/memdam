
import sys
import concurrent.futures
import Queue

import PyQt4.QtCore
import PyQt4.QtGui

import memdam
import memdam.common.error

_QAPP = None

def app():
    global _QAPP
    #inst = PyQt4.QtGui.QApplication.instance()
    #if inst is None:
    #    _QAPP = MyQApp(sys.argv[:1])
    #else:
    #    _QAPP = inst
    if _QAPP == None:
        _QAPP = MyQApp(sys.argv[:1])
    return _QAPP

class MyQApp(PyQt4.QtGui.QApplication):
    
    def __init__(self, *args, **kwargs):
        PyQt4.QtGui.QApplication.__init__(self, *args, **kwargs)
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
            PyQt4.QtCore.QTimer.singleShot(0, self.process_external_commands)

    def add_task(self, func):
        future = concurrent.futures.Future()
        self._task_queue.put((func, future))
        return future
    