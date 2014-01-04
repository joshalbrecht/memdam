
import memdam
import memdam.recorder.workmanager

def _work_generator(shutdown_queue, work_queue, source=None, dest=None):
    try:
        memdam.log.info((shutdown_queue, work_queue, source, dest))
    except Exception, e:
        x = str(e)
        import traceback
        traceback.print_exc(e)
        y = 4

def _work_consumer(work_queue, source=None, dest=None):
    try:
        memdam.log.info((work_queue, source, dest))
    except Exception, e:
        x = str(e)
        import traceback
        traceback.print_exc(e)
        y = 4

class EventstoreSynchronizer(memdam.recorder.workmanager.PollingWorkManager):
    """
    Synchronizes events from one store to another
    """

    def __init__(self, source, dest):
        memdam.recorder.workmanager.PollingWorkManager.__init__(self, "EventstoreSynchronizer", _work_generator, _work_consumer, kwargs=dict(source=source, dest=dest))
