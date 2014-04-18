
import os
import tempfile
import shutil
import subprocess

from PIL import Image

import memdam
import memdam.common.event
import memdam.recorder.collector.collector

class WebcamCollector(memdam.recorder.collector.collector.Collector):
    """
    Uses a simple external program (fswebcam) to capture the snapshots.

    Note: if this fails, can probably use VLC instead, see here:
    https://forum.videolan.org/viewtopic.php?f=2&t=108670
    works on windows too...

    And there are a ton of other programs too (streamer, webcam, cheese)
    """

    def __init__(self, config=None, state_store=None, eventstore=None, blobstore=None):
        memdam.recorder.collector.collector.Collector.__init__(self, config=config, state_store=state_store, eventstore=eventstore, blobstore=blobstore)
        self._last_image = None
        self._threshold = 5.0  #set empirically based on my webcam. Seems to have around 2.3 to 2.5 values when nothing is changing in the environment

    def _collect(self, limit):
        size_x, size_y = (1280, 1024)
        handle, snapshot_file = tempfile.mkstemp('.png')
        command = 'fswebcam -q -r %dx%d --png 9 -D 1 -S 7 --no-banner %s' % (size_x, size_y, snapshot_file)
        subprocess.check_call(command, shell=True)
        os.close(handle)
        memdam.log().debug("Saved " + snapshot_file + " (Size: " + str(size_x) + " x " + str(size_y) + ")")

        if os.path.getsize(snapshot_file) <= 0:
            memdam.log().warn("Failed to capture webcam image")
            return []

        if self._is_similar_to_last_image(snapshot_file):
            os.remove(snapshot_file)
            return []

        copied_location = memdam.common.utils.make_temp_path()
        shutil.copy(snapshot_file, copied_location)
        self._last_image = copied_location
        snapshot = self._save_file(snapshot_file, consume_file=True)
        return [memdam.common.event.new(u"com.memdam.webcam", data__file=snapshot)]

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
        memdam.log().debug("SNAPSHOT DIFFERENCE=%s", difference)
        return difference < self._threshold
