
"""
Convenience functions for parallel processing in python
"""

import Queue
import multiprocessing
import threading
import logging

from fn.monad import Option

import memdam
import memdam.common.log
import memdam.common.error

def setup_log(level=logging.WARN, handlers=None, queue=None):
    """
    Call from the beginning of the main thread.

    :param is_parent: True iff this is the main process, False otherwise
    :type  is_parent: bool
    """
    logging.basicConfig()
    if queue == None:
        queue = multiprocessing.Queue(-1)
        handler = memdam.common.log.ParentLogHandler(handlers, queue)
    else:
        assert handlers == None, "Can only configure handlers at the root logger"
        handler = memdam.common.log.ChildLogHandler(queue)
    memdam._logger = memdam.create_logger([handler], level)

def _setup_logging_and_call(*args, **kwargs):
    """
    Configures logging and calls the actual function.
    Also ensures that any uncaught exceptions are reported.
    """
    try:
        args = list(args)
        target = args.pop(0)
        queue = args.pop(0)
        #HACK: don't bother setting up a new logger if we're just in a different thread
        if not hasattr(memdam._logger.handlers[0], 'queue'):
            if not memdam.config.debug_logging:
                assert queue != None
                setup_log(queue)
        target(*args, **kwargs)
    except Exception, e:
        memdam.common.error.report(e)

class ProcessLikeThread(threading.Thread):
    """
    A Thread class that is more like a process.
    Can't be terminated
    """

    def run(self):
        try:
            threading.Thread.run(self)
            self.exitcode = 0
        except Exception, e:
            self.exitcode = 1
            raise e

    def terminate(self):
        """Prevent people from terminating threads"""
        raise Exception("Cannot terminate a thread!")

def create_strand(name, target, args=None, kwargs=None, use_process=False):
    """
    Use this to create a multiprocessing.Process.
    Handles log configuration.
    Must call setup_log() from the main process before calling this.

    :param target: the function to call. Must be a top-level function so that it can be pickled.
    :type  target: function
    :param args: all data you want to pass to target
    :type  args: iterable
    :param kwargs: all data you want to pass to target
    :type  kwargs: dict
    :param use_process: True iff you want to launch a process instead of a thread. Not that even if
    you specify True, may not launch a process if memdam.config.debug_processes is set
    :type  use_process: bool
    """
    if memdam.is_threaded_logging_setup():
        queue = memdam._logger.handlers[0].queue
    else:
        if memdam.config.debug_logging:
            queue = None
        else:
            raise Exception("setup_log() must be called before calling create_strand()")
    kwargs = Option.from_value(kwargs).get_or({})
    args = [target, queue] + list(Option.from_value(args).get_or(()))
    if not use_process or memdam.config.debug_processes:
        return ProcessLikeThread(name=name, target=_setup_logging_and_call, args=args, kwargs=kwargs)
    else:
        return multiprocessing.Process(name=name, target=_setup_logging_and_call, args=args, kwargs=kwargs)

def read_next_from_queue(queue):
    """
    Read exactly one record from the queue.
    :returns: list of records. If size is zero, the queue was shutdown or we encountered (and
    consumed) a memdam.common.poisonpill.PoisonPill and so should shutdown.
    :rtype: list
    """
    return _load_from_queue(queue, reinsert_poison_pills=False, block=True, max_size=1)

def read_all_from_queue(queue, max_size=None):
    """
    Loads all records from a queue (except memdam.common.poisonpill.PoisonPill's). Use this when
    emptying the queue during shutdown or something similar. Has no good way of notifying you that
    the queue was shutdown.
    :param max_size: how many objects to put in the list to return before returning it.
    :type  max_size: int
    """
    return _load_from_queue(queue, max_size=max_size)

def _load_from_queue(queue, reinsert_poison_pills=True, ignore_queue_closed=True, block=False, max_size=None):
    """
    Use this to safely pull items out of a multiprocessing queue.
    NO LOGGING IN THIS FUNCTION--it is used by the implementation of our loggers.

    :param reinsert_poison_pills: iff True, put any memdam.common.poisonpill.PoisonPill objects back
    in the queue when encountered. This should be used by anything accessing the queue EXCEPT for
    the main worker strands (which should be shutdown by those). iff False, does NOT put the
    memdam.common.poisonpill.PoisonPill back, but simply returns whatever is in the queue.
    :type  reinsert_poison_pills: bool
    :param ignore_queue_closed: iff True, will not throw exceptions when the queue is closed, and
    will simply return the current records.
    :type  ignore_queue_closed: bool
    :param block: iff True, will block until an object is pulled from the queue. Use this for the
    main workers. In this case, the ONLY way an empty set of records will be returned is if the
    queue is closed. iff False, may return an empty set of records that does NOT mean the queue was
    closed.
    :type  block: bool
    :param max_size: how many objects to put in the list to return before returning it.
    :type  max_size: int
    :returns: a list of the records fetched from the queue. Will not contain any
    memdam.common.poisonpill.PoisonPill objects.
    :rtype: list
    """
    records = []
    if block:
        poll_func = queue.get
    else:
        poll_func = queue.get_nowait
    while True:
        if max_size != None and len(records) >= max_size:
            return records
        try:
            try:
                try:
                    record = poll_func()
                except IOError, e:
                    if str(e) == "handle out of range in select()" and ignore_queue_closed:
                        return records
                    raise
                if isinstance(record, memdam.common.poisonpill.PoisonPill):
                    if reinsert_poison_pills:
                        queue.put(record)
                    return records
                records.append(record)
            except Queue.Empty:
                return records
        except (KeyboardInterrupt, SystemExit):
            raise
        except EOFError:
            return records
