
import shutil
import os
import tempfile

from PIL import Image

import memdam
import memdam.common.error
import memdam.common.utils
import memdam.common.event
import memdam.common.parallel
import memdam.common.image
import memdam.recorder.collector.collector
import memdam.recorder.application

class ScreenshotCollector(memdam.recorder.collector.collector.Collector):
    """
    Collects screenshots by using PyQT
    """

    def __init__(self, config=None, state_store=None, eventstore=None, blobstore=None):
        memdam.recorder.collector.collector.Collector.__init__(self, config=config, state_store=state_store, eventstore=eventstore, blobstore=blobstore)
        self._last_image = None
        self._threshold = 1.0

    def _snapshot_func(self):
        '''Needs to be called from the main thread so that it can take a screenshot of the desktop'''
        try:
            import PyQt4.QtGui
            _, screenshot_file = tempfile.mkstemp(".png")
            PyQt4.QtGui.QPixmap.grabWindow(PyQt4.QtGui.QApplication.desktop().winId()).save(screenshot_file, 'png')
            memdam.log().debug("Saved screenshot to " + screenshot_file)
            if self._is_similar_to_last_image(screenshot_file):
                os.remove(screenshot_file)
                return []
            copied_location = memdam.common.utils.make_temp_path()
            shutil.copy(screenshot_file, copied_location)
            self._last_image = copied_location
            screenshot = self._save_file(screenshot_file, consume_file=True)
            return [memdam.common.event.new(u"com.memdam.screenshot", data__file=screenshot)]
        except Exception, e:
            memdam.common.error.report(e)
            raise

    def _collect(self, limit):
        future = memdam.recorder.application.app().add_task(self._snapshot_func)
        return future.result()

    def _is_similar_to_last_image(self, screenshot):
        '''
        :param screenshot: the image to check for similarity against our previous capture
        :type  screenshot: string(path)
        :returns: True iff the image is sufficiently similar to the last one we took.
        :rtype: boolean
        '''
        if self._last_image is None:
            return False
        difference = memdam.common.image.rmsdiff(Image.open(self._last_image), Image.open(screenshot))
        return difference < self._threshold

    def stop(self):
        if self._last_image:
            os.remove(self._last_image)
