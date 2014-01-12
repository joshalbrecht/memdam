
import os
import time
import logging

import nose.tools

import memdam.common.utils
import memdam.common.parallel
import memdam.common.event
import memdam.common.query
import memdam.blobstore.localfolder
import memdam.eventstore.sqlite
import memdam.recorder.collector.collector
import memdam.recorder.sync

NAMESPACE = u"test.namespace"

class TestCollector(memdam.recorder.collector.collector.Collector):
    def collect(self, blobstore, limit):
        file_path = memdam.common.utils.make_temp_path()
        with open(file_path, 'wb') as outfile:
            outfile.write("some random data")
        blob_ref_a = self._save_file(file_path, blobstore, consume_file=False)
        blob_ref_b = self._save_file(file_path, blobstore, consume_file=True)
        TestCollector.events = [
            memdam.common.event.new(NAMESPACE, text__raw=buffer("mime and garbage"), attachment_one__file=blob_ref_a, to__text=u"thejash,someguy,etc"),
            memdam.common.event.new(NAMESPACE, text__raw=buffer("blah blah whatever"), attachment_one__file=blob_ref_b, attachment_two__file=blob_ref_a, to__text=u"someoneelse")
        ]
        return TestCollector.events

def test_sync():
    handlers = [memdam.STDOUT_HANDLER]
    memdam.common.parallel.setup_log("synch_test", handlers=handlers, level=logging.DEBUG)
    event_source_folder = memdam.common.utils.make_temp_path()
    assert not os.path.exists(event_source_folder)
    os.mkdir(event_source_folder)
    event_source = memdam.eventstore.sqlite.Eventstore(event_source_folder)
    event_dest_folder = memdam.common.utils.make_temp_path()
    os.mkdir(event_dest_folder)
    event_dest = memdam.eventstore.sqlite.Eventstore(event_dest_folder)
    blob_source_folder = memdam.common.utils.make_temp_path()
    os.mkdir(blob_source_folder)
    blob_dest_folder = memdam.common.utils.make_temp_path()
    os.mkdir(blob_dest_folder)
    blob_source = memdam.blobstore.localfolder.Blobstore(blob_source_folder)
    blob_dest = memdam.blobstore.localfolder.Blobstore(blob_dest_folder)
    collector = TestCollector()
    synchronizer = memdam.recorder.sync.Synchronizer(event_source, event_dest, blob_source, blob_dest)
    synchronizer.start()
    time.sleep(1.0)
    collector.collect_and_persist(event_source, blob_source)
    time.sleep(10.0)
    synchronizer.stop()
    #check that there are no events or blobs in the source stores
    nose.tools.eq_(len(event_source.find(memdam.common.query.Query())), 0)
    nose.tools.eq_(_count_blobs(blob_source._folder), 0)
    #check that the data in the dest stores is correct
    nose.tools.eq_(set(event_dest.find(memdam.common.query.Query())), set(TestCollector.events))
    nose.tools.eq_(_count_blobs(blob_dest._folder), 2)

def _count_blobs(blobstore_folder):
    """:returns: the number of blob files in the folder"""
    num_blobs = 0
    for (_, _, filenames) in os.walk(blobstore_folder):
        num_blobs += len(filenames)
    return num_blobs

if __name__ == '__main__':
    test_sync()
    memdam.shutdown_log()
