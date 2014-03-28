
import re
import types
import os
import os.path
import sys
import logging
import functools

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
#note: just for pylint
log.trace = lambda x: None
hack_logger(log)

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

#some debugging tools:

def debugrepr(obj, complete=True):
    """
    Converts any object into SOME reasonable kind of representation for debugging purposes.
    """
    if complete and hasattr(obj, '_debugrepr'):
        return obj._debugrepr()
    if isinstance(obj, basestring):
        if len(obj) > 128:
            return obj[:64] + '...' + obj[-64:]
        return obj
    if hasattr(obj, '__len__'):
        if len(obj) > 4:
            to_serialize = obj[:2] + ['...'] + obj[-2:]
        else:
            to_serialize = obj
        return '[%s]' % (', '.join(debugrepr(inner) for inner in to_serialize))
    return repr(obj)

_FILE_LINES = {}
def _get_file_lines_and_cache(file_name):
    if file_name not in _FILE_LINES:
        with open(file_name, 'rb') as infile:
            _FILE_LINES[file_name] = infile.readlines()
    return _FILE_LINES[file_name]

#TODO: maybe someday have a difference between full traces and lighter traces (in terms of the amount of data logged for each). Would make it more useful for 3rd party modules too, could even log all of their stuff.
_TRACE_EXPRESSIONS = None
_TRACE_MATCHES = {}
def _get_and_cache_trace_list_matched(file_name):
    global _TRACE_EXPRESSIONS
    if _TRACE_EXPRESSIONS is None:
        #this is here to avoid the silly race condition where two threads run the previous line together, before running the next one. By making a separate array and assigning to _TRACE_MATCHES, it should be atomic and we should get a single consistent array...
        expressions = []
        if 'TRACE_FILE' in os.environ:
            trace_file = os.environ['TRACE_FILE']
            with open(trace_file, 'rb') as infile:
                for line in infile.readlines():
                    expressions.append(re.compile(line))
        _TRACE_EXPRESSIONS = expressions
    if file_name not in _TRACE_MATCHES:
        result = False
        for expr in _TRACE_EXPRESSIONS:
            if expr.match(file_name):
                result = True
                break
        _TRACE_MATCHES[file_name] = result
    return _TRACE_MATCHES[file_name]

def _log_entrance_and_exit(f, *args, **kwargs):
    current_frame = sys._getframe()
    if current_frame.f_back is None or current_frame.f_back.f_back is None:
        caller_file_name = '(top)'
        caller_line_number = -1
    else:
        calling_frame = current_frame.f_back.f_back
        calling_code = calling_frame.f_code
        caller_file_name = calling_code.co_filename
        caller_line_number = calling_frame.f_lineno
    callee_file_name = f.__code__.co_filename
    caller_should_be_traced = _get_and_cache_trace_list_matched(caller_file_name)
    callee_should_be_traced = _get_and_cache_trace_list_matched(callee_file_name)
    trace_list_matched = caller_should_be_traced or callee_should_be_traced
    is_restricted_name = f.__name__ == '_debugrepr'
    should_log = trace_list_matched and not is_restricted_name
    if should_log:
        caller_file_lines = _get_file_lines_and_cache(caller_file_name)
        call_line = caller_file_lines[caller_line_number-1].strip()
        log.trace('%s:%s \\/ %s' % (caller_file_name, caller_line_number, call_line))
        for i in range(0, len(args)):
            log.trace('    %d = %s' % (i+1, debugrepr(args[i])))
        for kwarg_name in kwargs:
            log.trace('    %s = %s' % (kwarg_name, debugrepr(kwargs[kwarg_name])))
    try:
        result = f(*args, **kwargs)
    except Exception, e:
        if should_log:
            log.trace('%s:%s /\\ %s' % (caller_file_name, caller_line_number, call_line))
            log.trace('    !! ' + e.__class__.__name__ + ": " + str(e))
        raise
    if should_log:
        log.trace('%s:%s /\\ %s' % (caller_file_name, caller_line_number, call_line))
        log.trace('    ' + debugrepr(result))
    return result

#TODO: would be ideal to split all of this out into its own standalone module for manipulating logging at runtime.
def tracer(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return _log_entrance_and_exit(f, *args, **kwargs)
    return wrapper

class Base(object):
    """
    Inherit from this class to automatically log the entrance and exit to functions.
    """
    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if hasattr(attr, '__call__'):
            @functools.wraps(attr)
            def wrapper(*args, **kwargs):
                return _log_entrance_and_exit(attr, *args, **kwargs)
            return wrapper
        else:
            return attr

    def _debugrepr(self):
        if hasattr(self, 'to_json'):
            return self.to_json()
        encoded_attrs = ['"%s": %s' % (attr, debugrepr(getattr(self, attr))) \
                         for attr in self.__dict__]
        return '%s({%s})' % (self.__class__.__name__, ', '.join(encoded_attrs))
