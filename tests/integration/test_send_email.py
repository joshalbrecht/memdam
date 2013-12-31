
"""Send a test email to the local server"""

import multiprocessing
import asyncore
import logging
import time

import memdam
import memdam.common.timeutils
import memdam.common.event
import memdam.recorder.message
import memdam.recorder.mailqueue
import memdam.server.smtp_server

ADDRESS = ('127.0.0.1', 8465)
DEVICE = "SuperTester"

class EmailTestServer(memdam.server.smtp_server.DebuggingServer):
    """Simple test server. Validates the first message and exits immediately"""
    def __init__(self, success_queue, listenAddress):
        memdam.server.smtp_server.DebuggingServer.__init__(self, listenAddress)
        self.success_queue = success_queue

    def process_message(self, peer, mailfrom, rcpttos, data):
        """Called when the email is received. Validates that we got something reasonable"""
        #TODO: validate the email
        self.success_queue.put(True)

def run_email_server(success_queue):
    """Run from another process and actually processes the emails. Exit with code 0 if success"""
    EmailTestServer(success_queue, ADDRESS)
    asyncore.loop()

def test_send_and_receive_email():
    """Integration test. Starts email server and queue and makes sure that emails are received"""
    success_queue = multiprocessing.Queue()
    #start the email server
    process = multiprocessing.Process(target=run_email_server, args=(success_queue,))
    process.start()
    #start the mail queue
    memdam.common.parallel.setup_log("email-integration", level=logging.DEBUG, handlers=[memdam.STDOUT_HANDLER])
    mail_queue = memdam.recorder.mailqueue.MailQueue(4, ["someone@somewhere.com"], ADDRESS)
    #send an email
    events = [
        memdam.common.event.new("somedatatype", some__text="asdfsd", x__text="d"),
        memdam.common.event.new("somedatatype", some__text="tryr", x__text="g98f"),
    ]
    message = memdam.recorder.message.Message(DEVICE, events)
    mail_queue.add_message(message)
    #check that it was received
    result = success_queue.get(True, 5.0)
    time.sleep(2.0)
    assert result
    process.terminate()
    #shut everything down nicely
    mail_queue.shutdown()
    success_queue.close()
    success_queue.join_thread()
    memdam.log.handlers[0]._shutdown()

if __name__ == '__main__':
    test_send_and_receive_email()
