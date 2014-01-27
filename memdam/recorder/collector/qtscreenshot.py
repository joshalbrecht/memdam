
import sys
import tempfile

import PyQt4.QtGui
import PyQt4.QtCore

import memdam
import memdam.common.event
import memdam.common.parallel
import memdam.recorder.collector.collector

class MyQApp(PyQt4.QtGui.QApplication):

    # Define a new signal called 'trigger' that has no arguments.
    trigger = PyQt4.QtCore.pyqtSignal()

    def connect_trigger(self):
        # Connect the trigger signal to a slot.
        self.trigger.connect(self.handle_trigger)
        
    def emit_trigger(self):
        # Emit the signal.
        self.trigger.emit()

    def handle_trigger(self):
        # Show that the slot has been called.
        memdam.log.info("Received trigger from the other thread")

class ScreenshotCollector(memdam.recorder.collector.collector.Collector):
    """
    Collects screenshots by using PyQT
    """

    #TODO: lol this does not belong here at all
    def start(self):
        self.app = MyQApp(sys.argv[:1])
        self.app.connect_trigger()
        self.strand = memdam.common.parallel.create_strand("qtmain", self.app.exec_, use_process=False)
        self.strand.start()

    def _collect(self, limit):
        self.app.emit_trigger()
        #_, screenshot_file = tempfile.mkstemp(".png")
        #PyQt4.QtGui.QPixmap.grabWindow(PyQt4.QtGui.QApplication.desktop().winId()).save(screenshot_file, 'png')
        #memdam.log.debug("Saved screenshot to " + screenshot_file)
        #screenshot = self._save_file(screenshot_file, consume_file=True)
        #return [memdam.common.event.new(u"com.memdam.screenshot", data__file=screenshot)]
        return []

if __name__ == '__main__':
    collector = ScreenshotCollector(1,1,1,1)
    collector.start()
    collector._collect(1)
