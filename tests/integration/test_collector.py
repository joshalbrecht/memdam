
import time
import shutil
import os
import asyncore
import multiprocessing

import memdam.common.timeutils
import memdam.recorder.message
import memdam.recorder.main
import memdam.eventstore.sqlite
import memdam.server.email_data_handler

DEVICE = "somedevice"
SMTP_ADDRESS = ('127.0.0.1', 8465)
TEMP_DIR = "/tmp/memdamFullTest"
NAMESPACE = "com.somedatatype"

def run_server():
    """Run the email server"""
    #delete any leftover data from the previous run
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.mkdir(TEMP_DIR)
    archive = memdam.eventstore.sqlite.Eventstore(TEMP_DIR)
    memdam.server.email_data_handler.EmailDataHandler(SMTP_ADDRESS, archive)
    asyncore.loop()

def test_collector_and_server():
    """
    Test everything together--the collector runs with super simple events and saves them to the
    server for a little while.
    """
    #start a process to run the server
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
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
    archive = memdam.eventstore.sqlite.Eventstore(TEMP_DIR)
    assert len(archive.find()) > 0

if __name__ == '__main__':
    test_collector_and_server()
