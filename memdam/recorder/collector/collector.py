
import memdam.common.error

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
    def __init__(self, config, state_store):
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
    def collect(self, limit):
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

    def collect_and_persist(self, eventstore, blobstore):
        #TODO: forgot the name for intmax
        for event in self.collect(1000000):
            try:
                new_event = _save_files_in_event(event, blobstore)
                eventstore.save([new_event])
            except Exception, e:
                memdam.common.error.report(e)
        self.post_collect()

#TODO: in event, note that all file string must be of the form (url_prefix/uuid.ext) so that files don't get duplicated into different uuids when being copied between blobstores
def _save_files_in_event(event, blobstore):
    """
    Convert any Event into one that ONLY has files on the server where we are about to create
    this Event by sending each of the files as blobs to the server.

    :param event: the event in which to look for files
    :type  event: memdam.common.event.Event
    :returns: a new Event, with the same id, and all __file attributes pointing to paths on
        self._server_url
    :rtype: memdam.common.event.Event
    """
    new_event_dict = {}
    for key in event.keys:
        value = event.get_field(key)
        if memdam.common.event.Event.field_type(key) == memdam.common.event.FieldType.FILE:
            if not value.startswith(blobstore.get_url_prefix()):
                blob_id, extension = event.get_file_data(key)
                assert value.startswith("file://"), "Can only work with events based on local files right now"
                path = value[len("file://")]
                value = blobstore.set_data_from_file(blob_id, extension, path)
        new_event_dict[key] = value
    return memdam.common.event.Event(**new_event_dict)
