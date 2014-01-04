
import time
import logging

import memdam.common.parallel
import memdam.eventstore.sqlite
import memdam.recorder.sync

def test_sync():
    handlers = [memdam.STDOUT_HANDLER]
    memdam.common.parallel.setup_log("synch_test", handlers=handlers, level=logging.DEBUG)
    source = memdam.eventstore.sqlite.Eventstore(":memory:")
    dest = memdam.eventstore.sqlite.Eventstore(":memory:")
    synchronizer = memdam.recorder.sync.EventstoreSynchronizer(source, dest)
    synchronizer.start()
    time.sleep(5.0)
    synchronizer.stop()
    memdam.shutdown_log()

if __name__ == '__main__':
    test_sync()
