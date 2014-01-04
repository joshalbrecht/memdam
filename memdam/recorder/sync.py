
import memdam
import memdam.common.query
import memdam.recorder.workmanager

class SyncWorker(memdam.recorder.workmanager.Worker):
    def __init__(self, event_source, event_dest, blob_source, blob_dest):
        memdam.recorder.workmanager.Worker.__init__(self)
        self._event_source = event_source
        self._event_dest = event_dest
        self._blob_source = blob_source
        self._blob_dest = blob_dest

    def _process(self, work_id):
        memdam.log.info("Processing event " + str(work_id))
        event = self._event_source.get(work_id)
        for blob_id in event.blob_ids:
            memdam.log.info("Processing blob " + str(work_id))
            #TODO: someday, can check for existence in dest first, so that we don't have to re-upload files
            self._blob_source.get_data_to_file()
            self._blob_dest.set_data_from_file()
        self._event_dest.save([event])
        self._event_source.delete([event])
        for blob_id in event.blob_ids:
            self._blob_source.delete(blob_id)

class SyncManager(memdam.recorder.workmanager.Manager):
    def __init__(self, source, dest):
        memdam.recorder.workmanager.Manager.__init__(self)
        self._source = source
        self._dest = dest
        self._returned_id_set = set()

    def _generate_work_ids(self):
        oldest_event_ids = self._get_oldest_event_ids()
        new_id_set = set()
        for event_id in oldest_event_ids:
            if event_id not in self._returned_id_set:
                new_id_set.add(event_id)
        self._returned_id_set = oldest_event_ids
        return new_id_set

    def _get_oldest_event_ids(self, limit=100):
        query = memdam.common.query.Query(order=[('time__time', True)], limit=limit)
        events = self._source.find(query)
        return set([event.id for event in events])

class Synchronizer(memdam.recorder.workmanager.PollingWorkManager):
    """
    Synchronizes blobs and events from one store to another. Always does blobs first to ensure
    availability of binaries references by events.
    """

    def __init__(self, event_source, event_dest, blob_source, blob_dest):
        memdam.recorder.workmanager.PollingWorkManager.__init__(self,
            SyncManager(event_source, event_dest),
            self._worker_generator(event_source, event_dest, blob_source, blob_dest))

    def _worker_generator(self, event_source, event_dest, blob_source, blob_dest):
        def gen():
            return SyncWorker(event_source, event_dest, blob_source, blob_dest)
        return gen
