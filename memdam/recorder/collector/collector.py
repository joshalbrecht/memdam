
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
        """

    def stop(self):
        """
        Will be called after all calls to collect are done, before the program shuts down.
        Use this to be nice and clean up files and device handles.
        Obviously not guaranteed that this will be called in the case of an unclean shutdown.
        """
