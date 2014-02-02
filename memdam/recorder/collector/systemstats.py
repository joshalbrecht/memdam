
import memdam.common.event
import memdam.recorder.collector.collector

class SystemStats(memdam.recorder.collector.collector.Collector):
    """
    A simple collector for statistics like CPU usage, memory usage, I/O events, etc
    """

    def _collect(self, limit):
        return [memdam.common.event.new(u"com.memdam.cpu", cpu__number__percent=0.2)]
