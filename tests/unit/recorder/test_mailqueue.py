
import time
import threading
# pylint: disable=E0611,W0611
from nose.tools import assert_raises, assert_equals

import memdam.common.parallel
import memdam.recorder.mailqueue

WORKERS = 5
TO_ADDRESSES = ['a@b.com', 'guy@mail.edu']
SMTP_ADDRESS = '127.0.0.1'
NUM_MESSAGES = 10

class SimpleMessage(object):
    num_sent = 0
    num_deleted = 0
    lock = threading.Lock()
    def send(self, to_addresses, smtp_address):
        with SimpleMessage.lock:
            SimpleMessage.num_sent += 1
    def delete(self):
        with SimpleMessage.lock:
            SimpleMessage.num_deleted += 1

def test_processing():
    """Check that the mail queue workers empty it and call the right methods and shutdown cleanly"""
    with UseThreadsAndSimpleLogging():
        mail_queue = memdam.recorder.mailqueue.MailQueue(WORKERS, TO_ADDRESSES, SMTP_ADDRESS)
        messages = [SimpleMessage() for i in range(0, NUM_MESSAGES)]
        for message in messages:
            mail_queue.add_message(message)
        time.sleep(10.0)
        assert_equals(SimpleMessage.num_sent, NUM_MESSAGES)
        assert_equals(SimpleMessage.num_deleted, NUM_MESSAGES)
        mail_queue.shutdown()

class SlowMessage(object):
    """Just sleeps for a while to simulate messages that take a while to send"""
    finished_sending = False
    def send(self, to_addresses, smtp_address):
        time.sleep(2.0)
        SlowMessage.finished_sending = True
    def delete(self): pass

def test_shutdown():
    """Check that the queue waits for all messages to be sent before shutting down"""
    with UseThreadsAndSimpleLogging():
        mail_queue = memdam.recorder.mailqueue.MailQueue(WORKERS, TO_ADDRESSES, SMTP_ADDRESS)
        message = SlowMessage()
        mail_queue.add_message(message)
        mail_queue.shutdown()
        assert_equals(SlowMessage.finished_sending, True)

class UseThreadsAndSimpleLogging(object):
    """Makes processes launch as threads and makes logging simpler via global configuration"""

    def __init__(self):
        pass

    def __enter__(self):
        memdam.config.debug_processes = True
        memdam.config.debug_logging = True
        return self

    def __exit__(self, ex_type, value, traceback):
        memdam.config.debug_processes = False
        memdam.config.debug_logging = False

if __name__ == '__main__':
    memdam.log.setLevel(memdam.TRACE)
    test_processing()
    test_shutdown()
