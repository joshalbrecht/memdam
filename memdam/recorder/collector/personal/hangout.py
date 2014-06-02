
import os
import datetime
import subprocess

import pytz

import memdam
import memdam.common.timeutils
import memdam.recorder.collector.folder

class Hangout(memdam.recorder.collector.folder.Folder):
    """
    Handles folder full of google hangout recordings. Special handling to get the date and time and additional details correct.
    """

    def __init__(self, config=None, state_store=None, eventstore=None, blobstore=None):
        memdam.recorder.collector.folder.Folder.__init__(self,
            config=dict(namespace=u'com.memdam.personal.computer.hangout', **config),
            state_store=state_store,
            eventstore=eventstore,
            blobstore=blobstore)

    def _get_created_time(self, file_path):
        return self._get_start_time_from_filename(file_path)

    def _get_modified_time(self, file_path):
        return self._get_start_time_from_filename(file_path) + datetime.timedelta(seconds=self._get_duration(file_path))

    def _generate_attributes(self, file_path):
        duration = self._get_duration(file_path)
        return dict(
            duration__number__seconds=duration,
        )

    def _get_start_time_from_filename(self, file_path):
        """
        :returns: the time at which the call started
        :rtype: datetime.datetime
        """
        year, month, day, hour, minute, second = os.path.basename(file_path).split(".")[0].split("_")
        return memdam.common.timeutils.local_time_to_utc(datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second)))

    def _get_duration(self, file_path):
        """
        :returns: the amount of time (in seconds) that the video stored at file_path lasts
        :rtype: float
        """
        result = subprocess.Popen(["ffprobe", file_path], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        duration_line = [x for x in result.stdout.readlines() if "Duration" in x][0]
        hours, minutes, seconds_and_millis = duration_line.split(": ")[1].split(",")[0].strip().split(":")
        seconds, millis = seconds_and_millis.split(".")
        return float(hours) * 3600.0 + float(minutes) * 60.0 + float(seconds) + float('0.'+millis)
