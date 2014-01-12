
import sys
import os
import uuid

import memdam.common.error
import memdam.common.field
import memdam.common.validation

class Collector(object):
    """
    Abstract class.
    Overriden by all collectors, which are responsible for gathering all types of data.
    One collector per related set of information to record.
    Generates events, which will be inserted into the EventQueue.

    :attr _config: immutable, user-defined configuration
    :type _config: dict
    :attr _state_store: a place to persist state about synchronization--have we been configured,
    when was the last time we ran, what ids have been synched, etc
    :type _state_store: memdam.recorder.collector.state.CollectorState
    """

    #TODO: when started, destroy all files in the temp workspace
    #TODO: assert that these kwargs are non-null, and add the blob and event stores
    def __init__(self, config=None, state_store=None):
        """
        Config is loaded initially and defines any custom configuration for this collector.
        An empty config will be provided if there was none defined by the user.
        """
        self._config = config
        self._state_store = state_store

    def start(self):
        """
        Will be called before any calls to collect.
        Override this function to set up any state, etc.
        If this throws an exception, the daemon will fail to start.
        Also recover and clean up from any unclean shutdown.
        """

    #TODO: rename to be protected (_ prefix)
    #TODO: don't actually need the limit parameter anymore I don't think?
    def collect(self, blobstore, limit):
        """
        Must run fairly quickly (below whatever sampling threshold is configured).
        If not, will effectively be called as frequently as possible.
        Simply return a list of Events.
        Will be called at whatever interval is configured.
        :param limit: the maximum number of events to return. This allows backpressure in the
        process, to slow down certain collectors that would otherwise overwelm the system.
        Will always be >= 0. If == 0, then this collector is effectively being skipped.
        :type  limit: int
        :returns: all of the events
        :rtype: list(memdam.common.event.Event)
        """

    def post_collect(self):
        """
        Called after the events returned by collect have been persisted into the event queue.
        At this point it is safe to mark those events as handled from the perspective of the
        collector.

        Also a good place for deleting files.
        """

    def stop(self):
        """
        Will be called after all calls to collect are done, before the program shuts down.
        Use this to be nice and clean up files and device handles.
        Obviously not guaranteed that this will be called in the case of an unclean shutdown.
        """

    #TODO: move these args into the constructor
    def collect_and_persist(self, eventstore, blobstore):
        for event in self.collect(blobstore, sys.maxsize):
            try:
                eventstore.save([event])
            except Exception, e:
                memdam.common.error.report(e)
        self.post_collect()

    def _save_file(self, file_path, blobstore, consume_file=False, generate_id=True):
        _, file_name = os.path.split(file_path)
        if generate_id == False:
            assert memdam.common.validation.BLOB_FILE_NAME_REGEX.match(file_name), "file name must be a hex encoded uuid with extension"
        if (generate_id == None and memdam.common.validation.BLOB_FILE_NAME_REGEX.match(file_name)) or generate_id == False:
            blob_id = uuid.UUID('.'.join(file_name.split('.')[:-1]))
        else:
            blob_id = uuid.uuid4()
        extension = unicode(file_name.split('.')[-1].lower())
        blob_ref = memdam.common.blob.BlobReference(blob_id, extension)
        blobstore.set_data_from_file(blob_ref, file_path)
        if consume_file:
            os.remove(file_path)
        return blob_ref
