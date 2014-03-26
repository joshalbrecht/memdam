
import sys
import tempfile

import memdam
import memdam.common.event
import memdam.common.parallel
import memdam.recorder.collector.collector
import memdam.recorder.application

class ScreenshotCollector(memdam.recorder.collector.collector.Collector):
    """
    Collects screenshots by using PyQT
    """

    def _collect(self, limit):
        def snapshot_func():
            #TODO: unsure if this needs to be here or can be outside
            import PyQt4.QtGui
            _, screenshot_file = tempfile.mkstemp(".png")
            PyQt4.QtGui.QPixmap.grabWindow(PyQt4.QtGui.QApplication.desktop().winId()).save(screenshot_file, 'png')
            memdam.log.debug("Saved screenshot to " + screenshot_file)
            screenshot = self._save_file(screenshot_file, consume_file=True)
            return [memdam.common.event.new(u"com.memdam.screenshot", data__file=screenshot)]    
        future = memdam.recorder.application.app().add_task(snapshot_func)
        return future.result()

if __name__ == '__main__':
    collector = ScreenshotCollector(1,1,1,1)
    collector.start()
    collector._collect(1)
