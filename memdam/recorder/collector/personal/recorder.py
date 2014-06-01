
import datetime

import mutagen.mp3

import memdam
import memdam.recorder.collector.folder

class Recorder(memdam.recorder.collector.folder.Folder):
    """
    Handles folder full of recordings. Special handling to get the date and time and additional details correct.
    """

    def __init__(self, config=None, state_store=None, eventstore=None, blobstore=None):
        memdam.recorder.collector.folder.Folder.__init__(self,
            config=dict(namespace=u'com.memdam.personal.conversation.audio', **config),
            state_store=state_store,
            eventstore=eventstore,
            blobstore=blobstore)

    def _get_created_time(self, file_path):
        return self._get_modified_time(file_path) - datetime.timedelta(seconds=self._get_duration(file_path))

    def _generate_attributes(self, file_path):
        duration = self._get_duration(file_path)
        return dict(
            duration__number__seconds=duration
        )

    def _get_duration(self, file_path):
        """
        :returns: the amount of time (in seconds) that the recording stored at file_path lasts
        :rtype: float
        """
        return mutagen.mp3.MP3(file_path).info.length
