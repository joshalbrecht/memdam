
import tempfile
import select

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
        _, snapshot_file = tempfile.mkstemp(".png")
        image.save(snapshot_file)
        snapshot = self._save_file(snapshot_file, consume_file=True)
        memdam.log().debug("Saved " + snapshot_file + " (Size: " + str(size_x) + " x " + str(size_y) + ")")

        return [memdam.common.event.new(u"com.memdam.webcam", data__file=snapshot)]
