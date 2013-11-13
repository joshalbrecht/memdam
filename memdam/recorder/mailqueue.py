
import multiprocessing

import memdam
import memdam.common.poisonpill
import memdam.common.error
import memdam.common.parallel

def _consume_messages(queue, to_addresses, smtp_address):
    """
    Continually consume messages from the queue and send them
    """
    while True:
        try:
            memdam.log.trace("Polling for another mail message")
            message = queue.get()
            if isinstance(message, memdam.common.poisonpill.PoisonPill):
                memdam.log.info("Got PoisonPill message, halting mail process")
                return
            #TODO: move these out to settings somewhere
            username = 'bcoe'
            password = 'foobar'
            message.send(to_addresses, smtp_address, username, password)
            message.delete()
        except Exception, e:
            memdam.common.error.report(e)

class MailQueue(object):
    """
    Dump messages here and they will eventually get delivered.
    Can configured the number of threads to be used for delivery, etc.
    Tell the messages that they were sent after they were sent so that they can clean up files, etc
    """
    def __init__(self, num_workers, to_addresses, smtp_address):
        self._messages = multiprocessing.Queue()
        self._pool = [
                memdam.common.parallel.create_process(
                    name="MailMan-" + str(x), target=_consume_messages,
                    args=(self._messages, to_addresses, smtp_address)) \
            for x in range(0, num_workers)]
        for process in self._pool:
            process.start()

    def add_message(self, message):
        """
        Add a message to the mail queue.

        IMPORTANT: DO NOT RETAIN A REFERENCE TO THE MESSAGE.

        The message will be sent to ANOTHER PROCESS for sending, so consider it dead after adding
        to the mail queue.

        Also, the message must be able to be pickled.
        """
        self._messages.put(message)

    def shutdown(self):
        """
        Blocks until all messages have been fully delivered and all threads have been stopped
        """
        for process in self._pool:
            memdam.log.debug("Adding PoisonPill")
            self._messages.put(memdam.common.poisonpill.PoisonPill())
        for process in self._pool:
            memdam.log.info("Waiting for %s" % (process))
            process.join()
            if process.exitcode != 0:
                memdam.log.warn("Unclean mail worker exit: " + str(process.exitcode))
        memdam.log.trace("Closing MailQueue queue")
        self._messages.close()
        self._messages.join_thread()
