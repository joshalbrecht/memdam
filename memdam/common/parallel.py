
"""
Convenience functions for parallel processing in python
"""

import multiprocessing
import threading
import logging

from fn.monad import Option

import memdam
import memdam.common.log
import memdam.common.error

def setup_log(name, level=logging.WARN, handlers=None, queue=None):
    """
    Call from the beginning of the main thread.

    :param is_parent: True iff this is the main process, False otherwise
    :type  is_parent: bool
    """
    if queue == None:
        queue = multiprocessing.Queue(-1)
        handler = memdam.common.log.ParentLogHandler(handlers, queue)
    else:
        assert handlers == None, "Can only configure handlers at the root logger"
        handler = memdam.common.log.ChildLogHandler(queue)
    memdam.log = memdam.create_logger([handler], level, name)

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
        if not hasattr(memdam.log.handlers[0], 'queue'):
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

def create_process(name, target, args=None, kwargs=None):
    """
    Use this to create a multiprocessing.Process.
    Handles log configuration.
    Must call setup_log() from the main process before calling this.

    :param target: the function to call. Must be a top-level function so that it can be pickled.
    :type  target: function
    :param args: all data you want to pass to target
    :type  args: iterable
    """
    if hasattr(memdam.log.handlers[0], 'queue'):
        queue = memdam.log.handlers[0].queue
    else:
        if memdam.config.debug_logging:
            queue = None
        else:
            raise Exception("setup_log() must be called before calling create_process()")
    kwargs = Option.from_value(kwargs).get_or({})
    args = [target, queue] + list(Option.from_value(args).get_or(()))
    if memdam.config.debug_processes:
        return ProcessLikeThread(name=name, target=_setup_logging_and_call, args=args, kwargs=kwargs)
    else:
        return multiprocessing.Process(name=name, target=_setup_logging_and_call, args=args, kwargs=kwargs)
