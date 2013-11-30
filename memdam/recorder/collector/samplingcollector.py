
import memdam
import memdam.recorder.collector.collector

class SamplingCollector(memdam.recorder.collector.collector.Collector):
    """
    A collector that periodically samples a value. The simplest type.

    Will be called at a higher priority than other collectors, to ensure that information is not
    missed.
    """

    def __init__(self, config, state_store):
        memdam.recorder.collector.collector.Collector.__init__(self, config, state_store)

    def collect(self, limit):
        if limit <= 0:
            memdam.log.error("SamplingCollector %s was skipped!" % (self))
        else:
            return self.sample()

    def sample(self):
        """
        Generate a bunch of events for the state of the system at this exact moment.
        Should not take very long at all.
        :returns: all of the events
        :rtype: list(memdam.common.event.Event)
        """
