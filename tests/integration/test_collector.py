
import os
import time
import multiprocessing

import memdam.common.timeutils
import memdam.common.query
import memdam.eventstore.sqlite
import memdam.recorder.config
import memdam.recorder.user.terminal
import memdam.recorder.main

import tests.integration

DEVICE = "somedevice"
NAMESPACE = "com.somedatatype"

#TODO: broken because the client is obviously sending events to the server. Need a way to pass through configuration like with the server
def test_collector_and_server():
    """
    Test everything together--the collector runs with super simple events and saves them to the
    server for a little while.
    """
    #start a process to run the server
    server_process, database_folder, username, password = tests.integration.start_server("test_collector_and_server")
    #wait a while for it to start
    time.sleep(5.0)
    #start the collector
    user = memdam.recorder.user.terminal.User()
    default_config = memdam.recorder.config.get_default_config('nothere')
    config = memdam.recorder.config.Config('also_not_a_file', username=username, password=password, **default_config.data)
    collector_process = multiprocessing.Process(target=memdam.recorder.main.run, args=(user, config))
    collector_process.start()
    #wait a while
    time.sleep(45)
    #kill both
    server_process.terminate()
    collector_process.terminate()
    #and check that some events were recorded
    archive = memdam.eventstore.sqlite.Eventstore(os.path.join(database_folder, username))
    assert len(archive.find(memdam.common.query.Query())) > 0

if __name__ == '__main__':
    test_collector_and_server()
