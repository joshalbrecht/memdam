
import os
import datetime

import pytz

import memdam
import memdam.common.timeutils
import memdam.recorder.collector.folder

class Narrative(memdam.recorder.collector.folder.Folder):
    """
    Handles special narrative folder structure to get the time out, because it is not stored in the EXIF headers :(
    """

    def __init__(self, config=None, state_store=None, eventstore=None, blobstore=None):
        memdam.recorder.collector.folder.Folder.__init__(self,
            config=dict(namespace=u'com.memdam.personal.narrative', recurse=True, filter="^.*\\.jpg$", **config),
            state_store=state_store,
            eventstore=eventstore,
            blobstore=blobstore)

    def _get_created_time(self, file_path):
        return self._get_time_from_filename(file_path)

    def _get_modified_time(self, file_path):
        return self._get_time_from_filename(file_path)

    def _get_time_from_filename(self, file_path):
        """
        :returns: the time at which the photo was created
        :rtype: datetime.datetime
        """
        day_folder, time_string = os.path.split(file_path)
        hour = time_string[:2]
        minute = time_string[2:4]
        second = time_string[4:6]
        month_folder, day = os.path.split(day_folder)
        year_folder, month = os.path.split(month_folder)
        _, year = os.path.split(year_folder)
        return datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second), tzinfo=pytz.UTC)
