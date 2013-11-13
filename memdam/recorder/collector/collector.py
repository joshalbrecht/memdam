
class Collector(object):
    """
    Abstract class.
    Overriden by all collectors, which are responsible for gathering all types of data.
    One collector per related set of information to record.
    Generates events, which will be inserted into the EventQueue.
    """

    def __init__(self, config):
        """
        Config is loaded initially and defines any custom configuration for this collector.
        An empty config will be provided if there was none defined by the user.
        """
        self.config = config

    def start(self):
        """
        Will be called before any calls to collect.
        Override this function to set up any state, etc.
        If this throws an exception, the daemon will fail to start.
        Also recover and clean up from any unclean shutdown.
        """

    def collect(self):
        """
        Must run fairly quickly (below whatever sampling threshold is configured).
        If not, will effectively be called as frequently as possible.
        Simply return a list of Events.
        Will be called at whatever interval is configured.
        """

    def stop(self):
        """
        Will be called after all calls to collect are done, before the program shuts down.
        Use this to be nice and clean up files and device handles.
        Obviously not guarantee that this will be called in the case of an unclean shutdown.
        """
