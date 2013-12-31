
import time
import shutil
import os
import asyncore
import multiprocessing

import memdam.common.timeutils
import memdam.recorder.message
import memdam.eventstore.sqlite
import memdam.server.email_data_handler

DEVICE = "somedevice"
SMTP_ADDRESS = ('127.0.0.1', 8465)
TEMP_DIR = "/tmp/memdamEmailRecvTest"
NAMESPACE = "somedatatype"

def test_email_handling():
    """
    Start a server and send it an email and check that some events get inserted correctly
    """
    #start a process to run the server
    process = multiprocessing.Process(target=run_server)
    process.start()
    time.sleep(5.0)
    #send the email
    events = [
        memdam.common.event.Event(memdam.common.timeutils.now(), NAMESPACE, some__text="asdfsd", x__text="d"),
        memdam.common.event.Event(memdam.common.timeutils.now(), NAMESPACE, some__text="tryr", x__text="g98f"),
    ]
    message = memdam.recorder.message.Message(DEVICE, events)
    #TODO: move these out to settings somewhere
    username = 'bcoe'
    password = 'foobar'
    message.send(["someone@domain.com"], SMTP_ADDRESS, username, password)
    #check that the events were actually inserted
    archive = memdam.eventstore.sqlite.SqliteArchive(TEMP_DIR)
    assert len(archive.find()) == 2
    process.terminate()

def run_server():
    """Run the email server"""
    #delete any leftover data from the previous run
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.mkdir(TEMP_DIR)
    archive = memdam.eventstore.sqlite.SqliteArchive(TEMP_DIR)
    memdam.server.email_data_handler.EmailDataHandler(SMTP_ADDRESS, archive)
    asyncore.loop()

if __name__ == '__main__':
    test_email_handling()
