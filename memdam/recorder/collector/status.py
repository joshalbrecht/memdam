
import memdam.common.event
import memdam.recorder.collector.collector

class ProcessStatusCollector(memdam.recorder.collector.collector.Collector):
    """
    Collects information about when the memdam process was even running.
    """

    def _collect(self, limit):
        return [memdam.common.event.new(u"com.memdam.process.status", is_running__boolean=True)]
