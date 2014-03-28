
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

#TODO: use a config file that defines modules that we are interested in. Any time a call is going into OR out of that module, log it, otherwise, ignore
#eg, that filename should be passed in with something like --trace-modules=filename.txt
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
    should_log = f.__name__ != '_debugrepr'
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
            log.trace('%s:%s !! %s' % (exception_file_name, exception_line_number, debugrepr(e)))
        raise e
    if should_log:
        log.trace('%s:%s /\\ %s' % (caller_file_name, caller_line_number, call_line))
        log.trace('    ' + debugrepr(result))
    return result

#TODO: would probably be good to make this purely opt-in, like the last flag in sys.argv has to be --debug or something...
#and apply that below as well
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

