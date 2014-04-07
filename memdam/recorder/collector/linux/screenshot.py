
import os
import tempfile
import subprocess

import memdam.common.event
import memdam.recorder.collector.collector

#TODO: delete this because the qt one works better
class ScreenshotCollector(memdam.recorder.collector.collector.Collector):
    """
    A simple collector of screenshots.
    """

    def _collect(self, limit):
        handle, screenshot_file = tempfile.mkstemp(".png")
        command = "import -window root %s" % (screenshot_file)
        subprocess.check_call(command, shell=True)
        screenshot = self._save_file(screenshot_file, consume_file=True)
        os.close(handle)
        return [memdam.common.event.new(u"com.memdam.screenshot", data__file=screenshot)]
