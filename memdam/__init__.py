
import types
import os
import os.path
import sys
import logging

#configure log formatting
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s %(process)d-%(threadName)s %(filename)s:%(lineno)d:%(message)s"
FORMATTER = logging.Formatter(DEFAULT_FORMAT)

#configure logging to stdout
STDOUT_HANDLER = logging.StreamHandler(sys.stdout)
STDOUT_HANDLER.setFormatter(FORMATTER)

#a custom logging level for logging ridiculous amounts of information when first testing functions
TRACE = 5

#add a trace level, because I am verbose
def trace(self, msg, *args, **kwargs):
    """
    Log "msg % args" with severity "TRACE".

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.trace("Houston, we are sending you a mesage: %s", "interesting problem", exc_info=1)
    """
    if self.isEnabledFor(TRACE):
        self._log(TRACE, msg, args, **kwargs)

def hack_logger(newlog):
    newlog.trace = types.MethodType(trace, newlog)

def create_logger(handlers, level, name):
    """
    Build a new logger given an iterable of handlers
    """
    newlog = logging.getLogger(name)
    newlog.setLevel(level)
    for handler in handlers:
        newlog.addHandler(handler)

    hack_logger(newlog)
    return newlog

#set up a default logger in case anything goes wrong before we've set up the real, multi-process
#logging
SIMPLE_LOGGER = create_logger([STDOUT_HANDLER], logging.WARN, name="default")
log = SIMPLE_LOGGER

def use_debug_logger():
    """Convenience function. Call this to log all statements (TRACE and above) to STDOUT"""
    global log
    log = create_logger([STDOUT_HANDLER], TRACE, name="testlogger")

#access these globals for runtime options (enable debugging, etc)
class Config(object):
    """a simple configuration object, before anything is loaded"""
    def __init__(self):
        self.debug_processes = False
        self.debug_logging = False
        self.mandrill_key = None
        userhome = os.path.expanduser("~")
        mandrill_key_file = os.path.join(userhome, ".mandrill")
        self.mandrill_key = None
        if os.path.exists(mandrill_key_file):
            infile = open(mandrill_key_file)
            self.mandrill_key = infile.read().strip()
            infile.close()
        else:
            log.warn("Could not find email api key!")
config = Config()

def flush_logs():
    """Simply write all of the log events out of the queue, for debugging"""
    log.handlers[0].flush()

def shutdown_log():
    """Should be the very last statement in a program. Without this there are warnings about unclean debug client shutdowns."""
    log.handlers[0]._shutdown()
    
def is_threaded_logging_setup():
    return hasattr(log.handlers[0], 'queue')


