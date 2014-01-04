
import memdam
import memdam.recorder.workmanager

class EventstoreSyncWorker(memdam.recorder.workmanager.Worker):
    def __init__(self, source, dest):
        memdam.recorder.workmanager.Worker.__init__(self)
        self._source = source
        self._dest = dest

    def _process(self, work_id):
        pass

class EventstoreSyncManager(memdam.recorder.workmanager.Manager):
    def __init__(self, source, dest):
        memdam.recorder.workmanager.Manager.__init__(self)
        self._source = source
        self._dest = dest

    def _generate_work_ids(self):
        return []

class EventstoreSynchronizer(memdam.recorder.workmanager.PollingWorkManager):
    """
    Synchronizes events from one store to another
    """

    def __init__(self, source, dest):
        memdam.recorder.workmanager.PollingWorkManager.__init__(self, EventstoreSyncManager(source, dest), self._worker_generator(source, dest))

    def _worker_generator(self, source, dest):
        def gen():
            return EventstoreSyncWorker(source, dest)
        return gen
