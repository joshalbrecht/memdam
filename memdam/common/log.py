
"""
Inspired by:
http://stackoverflow.com/questions/641420/how-should-i-log-while-using-multiprocessing-in-python

Do not use this directly.
Use the wrappers in parallel.
"""

import threading
import logging
import sys
import traceback
import Queue
import atexit

import memdam
import memdam.common.poisonpill

class ChildLogHandler(logging.Handler):
    """
    Puts messages into a queue that will be handled by the parent process.
    """

    def __init__(self, queue):
        logging.Handler.__init__(self)
        logging.Handler.setFormatter(self, memdam.FORMATTER)
        self.queue = queue

    def send(self, message):
        """
        Send a mesage to the parent logger
        """
        self.queue.put_nowait(message)

    def _format_record(self, record):
        """
        ensure that exc_info and args
        have been stringified.  Removes any chance of
        unpickleable things inside and possibly reduces
        message size sent over the pipe
        """
        if record.args:
            record.msg = record.msg % record.args
            record.args = None
        if record.exc_info:
            dummy = self.format(record)
            record.exc_info = None

        return record

    def setFormatter(self, fmt):
        raise Exception("Different formats are disabled because they must be synchronized between children and parent.")

    def emit(self, record):
        try:
            data = self._format_record(record)
            self.send(data)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

class ParentLogHandler(ChildLogHandler):
    """
    Collects all logs from child processes and sends them to a set of handlers at the parent.

    Note: this flushes the logs at exit, but be sure not to register any other atexit calls which
    might make logging calls BEFORE creating this log handler, otherwise there is no guarantee that
    the messages will be written!
    """

    def __init__(self, handlers, queue):
        ChildLogHandler.__init__(self, queue)
        self._handlers = handlers
        for handler in self._handlers:
            handler.setFormatter(memdam.FORMATTER)
        self._thread = threading.Thread(target=self.receive)
        self._thread.daemon = True
        self._thread.start()
        atexit.register(self._shutdown)

    def _shutdown(self):
        """
        Called right before the process terminates
        """
        if self._thread != None:
            self.queue.put(memdam.common.poisonpill.PoisonPill())
            self._thread.join()
            self.queue.close()
            self.queue.join_thread()
            self._thread = None

    def receive(self):
        """
        Continually receive messages from the child processes
        """
        while True:
            try:
                records = memdam.common.parallel.read_next_from_queue(self.queue)
                if len(records) <= 0:
                    break
                assert len(records) == 1
                for handler in self._handlers:
                    handler.emit(records[0])
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                traceback.print_exc(file=sys.stderr)

    def flush(self):
        """
        Print all messages currently in the queue. Does not block.
        """
        try:
            records = memdam.common.parallel.read_all_from_queue(self.queue)
            for record in records:
                for handler in self._handlers:
                    handler.emit(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            traceback.print_exc(file=sys.stderr)

    def close(self):
        for handler in self._handlers:
            handler.close()
        logging.Handler.close(self)

    def emit(self, record):
        ChildLogHandler.emit(self, record)
        self.flush()
