
import tempfile
import subprocess

import memdam.common.event
import memdam.recorder.collector.collector

class ScreenshotCollector(memdam.recorder.collector.collector.Collector):
    """
    A simple collector of screenshots.
    """

    def collect(self, blobstore, limit):
        screenshot_file, _ = tempfile.mkstemp(".png")
        command = "import -window root %s" % (screenshot_file)
        subprocess.check_call(command, shell=True)
        screenshot = self._save_file(screenshot_file, blobstore, consume_file=True)
        return [memdam.common.event.new(u"com.memdam.screenshot", data__file=screenshot)]
