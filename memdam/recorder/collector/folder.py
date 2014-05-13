
import os
import glob
import datetime

import pytz

import memdam
import memdam.common.timeutils
import memdam.common.event
import memdam.recorder.collector.collector

class Folder(memdam.recorder.collector.collector.Collector):
    """
    Uploads each file from a folder as a new event.

    Optionally deletes older files that have not changed in a while.

    Has a slight delay in case you are writing a file for the very first time,
    in which case we would not want to upload just part of the whole file.
    """

    def __init__(self, config=None, state_store=None, eventstore=None, blobstore=None):
        memdam.recorder.collector.collector.Collector.__init__(self, config=config, state_store=state_store, eventstore=eventstore, blobstore=blobstore)
        self._namespace = config.get('namespace')
        self._folder = config.get('folder')
        self._seconds_before_upload = datetime.timedelta(seconds=config.get('seconds_before_upload', 30.0))
        current_state = self._state_store.get_state()
        if current_state.get('last_modified', None) is None:
            current_state['last_modified'] = {}
            self._state_store.set_state(current_state)
        self._files_collected = []

    @memdam.vdebug()
    def _collect(self, limit):
        self._files_collected = []
        #TODO: should probably parallelize this loop...
        #TODO: should probably be able to return futures from _collect so that we don't have to block forever
        #TODO: probably want options about which files to include, whether to be recursive, etc
        return [self._make_event(file_path) for file_path in glob.glob(self._folder + '/*') if self._include_file(file_path)]

    @memdam.vtrace()
    def _include_file(self, file_path):
        last_modified_time = self._get_modified_time(file_path)
        now = memdam.common.timeutils.now()
        time_when_ok_to_upload = last_modified_time + self._seconds_before_upload
        #RESUME: test failing because files have been too recently modified. Change mtime in test?
        if now < time_when_ok_to_upload:
            return False
        previous_modified_time = self._state_store.get_state()['last_modified'].get(file_path, None)
        if previous_modified_time is None:
            return True
        else:
            #this is dumb. saving as strings to prevent worries about float differences
            return str(previous_modified_time) != str(last_modified_time)

    #TODO: make child classes that do something better for get_created_time:
    #for recorder, look at mtime - length
    #for google hangouts, use file name as time
    #for calls, use file name as time
    def _get_created_time(self, file_path):
        return datetime.datetime.fromtimestamp(os.path.getctime(file_path), pytz.UTC)

    def _get_modified_time(self, file_path):
        return datetime.datetime.fromtimestamp(os.path.getmtime(file_path), pytz.UTC)

    @memdam.vtrace()
    def _make_event(self, file_path):
        last_modified_time = self._get_modified_time(file_path)
        created_time = self._get_created_time(file_path)
        folder_path, file_name = os.path.split(file_path)
        file_size = os.path.getsize(file_path)
        blob = self._save_file(file_path, consume_file=False)
        event = memdam.common.event.new(
            self._namespace,
            time__time=created_time,
            modified__time=last_modified_time,
            data__file=blob,
            name__string=file_name,
            size__long=file_size)
        #TODO: perhaps add extra details for specific types of files? format, mime type, movie length, codecs, resolution, etc
        self._files_collected.append((file_path, last_modified_time))
        return event

    def post_collect(self):
        current_state = self._state_store.get_state()
        modification_times = current_state['last_modified']
        for file_path, last_modified_time in self._files_collected:
            modification_times[file_path] = str(last_modified_time)
            #TODO: eventually delete from folder (not yet, not sure if everything is in there)
        current_state['last_modified'] = modification_times
        self._state_store.set_state(current_state)
