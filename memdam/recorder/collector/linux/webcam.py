
import os
import tempfile
import select
import shutil

from PIL import Image
#from here: https://github.com/gebart/python-v4l2capture/
import v4l2capture

import memdam
import memdam.common.event
import memdam.recorder.collector.collector

class WebcamCollector(memdam.recorder.collector.collector.Collector):
    """
    Collect snapshots from the webcam using some janky V4L2 library.

    Note: if this fails, can probably use VLC instead, see here:
    https://forum.videolan.org/viewtopic.php?f=2&t=108670
    works on windows too...
    """

    def __init__(self, config=None, state_store=None, eventstore=None, blobstore=None):
        memdam.recorder.collector.collector.Collector.__init__(self, config=config, state_store=state_store, eventstore=eventstore, blobstore=blobstore)
        self._last_image = None
        self._threshold = 2.1  #set empirically based on my webcam. Seems to have around 1.3 to 1.9 values when nothing is changing in the environment

    def _collect(self, limit):
        # Open the video device.
        video = v4l2capture.Video_device("/dev/video0")

        # Suggest an image size to the device. The device may choose and
        # return another size if it doesn't support the suggested one.
        size_x, size_y = video.set_format(1280, 1024)

        # Create a buffer to store image data in. This must be done before
        # calling 'start' if v4l2capture is compiled with libv4l2. Otherwise
        # raises IOError.
        video.create_buffers(1)

        # Send the buffer to the device. Some devices require this to be done
        # before calling 'start'.
        video.queue_all_buffers()

        # Start the device. This lights the LED if it's a camera that has one.
        video.start()

        # Wait for the device to fill the buffer.
        select.select((video,), (), ())

        # The rest is easy :-)
        image_data = video.read()
        video.close()
        image = Image.fromstring("RGB", (size_x, size_y), image_data)
        handle, snapshot_file = tempfile.mkstemp(".png")
        image.save(snapshot_file)
        os.close(handle)
        memdam.log().debug("Saved " + snapshot_file + " (Size: " + str(size_x) + " x " + str(size_y) + ")")

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
