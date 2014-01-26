
import sys
import tempfile

import PyQt4.QtGui

import memdam
import memdam.common.event
import memdam.recorder.collector.collector

class ScreenshotCollector(memdam.recorder.collector.collector.Collector):
    """
    Collects screenshots by using PyQT
    """

    #TODO: lol this does not belong here at all
    def start(self):
        self.app = PyQt4.QtGui.QApplication(sys.argv[:1])

    def _collect(self, limit):
        _, screenshot_file = tempfile.mkstemp(".png")
        PyQt4.QtGui.QPixmap.grabWindow(PyQt4.QtGui.QApplication.desktop().winId()).save(screenshot_file, 'png')
        memdam.log.debug("Saved screenshot to " + screenshot_file)
        screenshot = self._save_file(screenshot_file, consume_file=True)
        return [memdam.common.event.new(u"com.memdam.screenshot", data__file=screenshot)]

if __name__ == '__main__':
    collector = ScreenshotCollector(1,1,1,1)
    collector.start()
    collector._collect(1)
