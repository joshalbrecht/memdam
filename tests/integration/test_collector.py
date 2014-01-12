
import time
import multiprocessing

import memdam.common.timeutils
import memdam.common.query
import memdam.recorder.main
import memdam.eventstore.sqlite

import tests.integration

DEVICE = "somedevice"
NAMESPACE = "com.somedatatype"

def test_collector_and_server():
    """
    Test everything together--the collector runs with super simple events and saves them to the
    server for a little while.
    """
    #start a process to run the server
    server_process, database_folder = tests.integration.start_server("test_collector_and_server")
    #wait a while for it to start
    time.sleep(5.0)
    #start the collector
    collector_process = multiprocessing.Process(target=memdam.recorder.main.main)
    collector_process.start()
    #wait a while
    time.sleep(45)
    #kill both
    server_process.terminate()
    collector_process.terminate()
    #and check that some events were recorded
    archive = memdam.eventstore.sqlite.Eventstore(database_folder)
    assert len(archive.find(memdam.common.query.Query())) > 0

if __name__ == '__main__':
    test_collector_and_server()
