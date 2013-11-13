
"""Send a test email to the local server"""

import sys
import multiprocessing
import asyncore
import logging

import memdam
import memdam.common.time
import memdam.common.event
import memdam.recorder.message
import memdam.recorder.mailqueue
import memdam.server.smtp_server

ADDRESS = ('127.0.0.1', 8465)
DEVICE = "SuperTester"

class EmailTestServer(memdam.server.smtp_server.DebuggingServer):
    """Simple test server. Validates the first message and exits immediately"""
    def __init__(self, listenAddress):
        memdam.server.smtp_server.DebuggingServer.__init__(self, listenAddress)

    def process_message(self, peer, mailfrom, rcpttos, data):
        """Called when the email is received. Validates that we got something reasonable"""
        #TODO: validate the email
        sys.exit(0)

def run_email_server():
    """Run from another process and actually processes the emails. Exit with code 0 if success"""
    EmailTestServer(ADDRESS)
    asyncore.loop()

def test_send_and_receive_email():
    """Integration test. Starts email server and queue and makes sure that emails are received"""
    #start the email server
    process = multiprocessing.Process(target=run_email_server)
    process.start()
    #start the mail queue
    memdam.common.parallel.setup_log("email-integration", level=logging.DEBUG, handlers=[memdam.STDOUT_HANDLER])
    mail_queue = memdam.recorder.mailqueue.MailQueue(4, ["someone@somewhere.com"], ADDRESS)
    #send an email
    events = [
        memdam.common.event.Event(memdam.common.time.now(), some_text="asdfsd", x_text="d"),
        memdam.common.event.Event(memdam.common.time.now(), some_text="tryr", x_text="g98f"),
    ]
    message = memdam.recorder.message.Message(DEVICE, events)
    mail_queue.add_message(message)
    #check that it was received
    process.join(5.0)
    assert process.exitcode == 0
    #shut everything down nicely
    mail_queue.shutdown()

if __name__ == '__main__':
    test_send_and_receive_email()
