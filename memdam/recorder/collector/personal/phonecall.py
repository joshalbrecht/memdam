
import os
import datetime

import pytz

import memdam
import memdam.recorder.collector.folder

class PhoneCall(memdam.recorder.collector.folder.Folder):
    """
    Handles folder full of call recordings. Special handling to get the date and time and additional details correct.
    """

    def __init__(self, config=None, state_store=None, eventstore=None, blobstore=None):
        memdam.recorder.collector.folder.Folder.__init__(self,
            config=dict(namespace=u'com.memdam.personal.phone.calls.audio', recurse=True, filter='^.*wav$', **config),
            state_store=state_store,
            eventstore=eventstore,
            blobstore=blobstore)

    def _get_created_time(self, file_path):
        return self._get_start_time_from_filename(file_path)

    def _get_modified_time(self, file_path):
        return self._get_start_time_from_filename(file_path) + datetime.timedelta(seconds=self._get_duration(file_path))

    def _generate_attributes(self, file_path):
        duration = self._get_duration(file_path)
        _, was_incoming, phone_number = self._parse_file_name(file_path)
        #strip the leading 1 off. This is a bit of a hack because I live in america and don't care about anyone in other countries...
        clean_phone_number = phone_number[-10:]
        return dict(
            duration__number__seconds=duration,
            was_incoming__bool=was_incoming,
            phone_number__string=clean_phone_number,
        )

    def _get_start_time_from_filename(self, file_path):
        """
        :returns: the time at which the call started
        :rtype: datetime.datetime
        """
        return self._parse_file_name(file_path)[0]

    def _parse_file_name(self, file_path):
        directory, file_name = os.path.split(file_path)
        file_name_no_extension = file_name.replace('.wav', '')
        _, timestamp, in_out, phone_number = file_name_no_extension.split('_')
        hour, minute, second = timestamp.split('-')
        _, folder = os.path.split(directory)
        year, month, day = folder.split('-')
        creation_time = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second), tzinfo=pytz.UTC)
        was_incoming = in_out == 'IN'
        return creation_time, was_incoming, phone_number

    def _get_duration(self, file_path):
        """
        :returns: the amount of time (in seconds) that the recording stored at file_path lasts
        :rtype: float
        """
        handle = open(file_path, "rb")

        #read the ByteRate field from file (see the Microsoft RIFF WAVE file format)
        #https://ccrma.stanford.edu/courses/422/projects/WaveFormat/
        #ByteRate is located at the first 28th byte
        handle.seek(28)
        a = handle.read(4)

        #convert string a into integer/longint value
        #a is little endian, so proper conversion is required
        byteRate = 0
        for i in range(4):
            byteRate = byteRate + ord(a[i]) * pow(256, i)

        #get the file size in bytes
        fileSize = os.path.getsize(file_path)

        #the duration of the data, in milliseconds, is given by
        millis = ((fileSize-44)*1000)/byteRate

        return float(millis) / 1000.0
