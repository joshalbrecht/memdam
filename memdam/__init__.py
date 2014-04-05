
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
def _trace(self, msg, *args, **kwargs):
    """
    Log "msg % args" with severity "TRACE".

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.trace("Houston, we are sending you a mesage: %s", "interesting problem", exc_info=1)
    """
    if self.isEnabledFor(TRACE):
        self._log(TRACE, msg, args, **kwargs)

def hack_logger(newlog):
    newlog.trace = types.MethodType(_trace, newlog)

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
#TODO: this log variable should be replaced with something that automatically calls the right get_logger
log = SIMPLE_LOGGER
#note: just for pylint
log.trace = lambda x: None
hack_logger(log)
logging.addLevelName(TRACE, "TRACE")

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

class LazyLoggingWrapperBase(object):
    '''
    Decorator for logging call/arguments and return value from functions.

    Can specify the log level, and a list of arguments that should be listed verbosely.
    '''
    def __init__(self, level, verbose=(), verbose_return=False):
        self.verbose = verbose
        self.level = level
        self.verbose_return = verbose_return

    def get_verbose(self, func):
        return self.verbose

    def __call__(self, func):
        verbose_arg_names = self.get_verbose(func)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            #TODO: restructure this function so that it is easier to step through when debugging
            if self.level == TRACE:
                log_func = log.trace
            elif self.level == logging.DEBUG:
                log_func = log.debug
            elif self.level == logging.INFO:
                log_func = log.info
            elif self.level == logging.WARN:
                log_func = log.warn
            elif self.level == logging.ERROR:
                log_func = log.error
            else:
                raise Exception("Bad logging level for lazy logger: " + str(self.level))
            current_frame = sys._getframe()
            if current_frame.f_back is None:
                caller_file_name = '(top)'
                caller_line_number = -1
            else:
                calling_frame = current_frame.f_back
                calling_code = calling_frame.f_code
                caller_file_name = calling_code.co_filename
                caller_line_number = calling_frame.f_lineno
            callee_file_name = func.__code__.co_filename
            func_name = callee_file_name + ':' + func.func_name
            log_func('%s:%s \\/ %s' % (caller_file_name, caller_line_number, func_name))
            for i in range(0, len(args)):
                log_func('    %d = %s' % (i+1, debugrepr(args[i])))
            for kwarg_name in kwargs:
                log_func('    %s = %s' % (kwarg_name, debugrepr(kwargs[kwarg_name])))
            try:
                result = func(*args, **kwargs)
            except Exception, e:
                log_func('%s:%s /\\ %s' % (caller_file_name, caller_line_number, func_name))
                log_func('    !! ' + e.__class__.__name__ + ": " + str(e))
                raise
            log_func('%s:%s /\\ %s' % (caller_file_name, caller_line_number, func_name))
            log_func('    ' + debugrepr(result))
            return result
        return wrapper

class VerboseLazyLoggingWrapper(LazyLoggingWrapperBase):
    '''
    Effectively inverts the verbosity list (can exclude things from being verbose, not include, by setting limit)
    '''

    def __init__(self, level, limit=(), verbose_return=True):
        LazyLoggingWrapperBase.__init__(self, level, verbose=(), verbose_return=verbose_return)
        self.limit = limit

    def get_verbose(self, func):
        '''Invert the list of argument names for the function'''
        all_names = set(func.func_code.co_varnames)
        return all_names - set(self.limit)

class trace(LazyLoggingWrapperBase):
    def __init__(self, verbose=(), verbose_return=False):
        LazyLoggingWrapperBase.__init__(self, TRACE, verbose=verbose, verbose_return=verbose_return)

class debug(LazyLoggingWrapperBase):
    def __init__(self, verbose=(), verbose_return=False):
        LazyLoggingWrapperBase.__init__(self, logging.DEBUG, verbose=verbose, verbose_return=verbose_return)

class info(LazyLoggingWrapperBase):
    def __init__(self, verbose=(), verbose_return=False):
        LazyLoggingWrapperBase.__init__(self, logging.INFO, verbose=verbose, verbose_return=verbose_return)

class warn(LazyLoggingWrapperBase):
    def __init__(self, verbose=(), verbose_return=False):
        LazyLoggingWrapperBase.__init__(self, logging.WARN, verbose=verbose, verbose_return=verbose_return)

class error(LazyLoggingWrapperBase):
    def __init__(self, verbose=(), verbose_return=False):
        LazyLoggingWrapperBase.__init__(self, logging.ERROR, verbose=verbose, verbose_return=verbose_return)

class vtrace(VerboseLazyLoggingWrapper):
    def __init__(self, limit=(), verbose_return=True):
        VerboseLazyLoggingWrapper.__init__(self, TRACE, limit=limit, verbose_return=verbose_return)

class vdebug(VerboseLazyLoggingWrapper):
    def __init__(self, limit=(), verbose_return=True):
        VerboseLazyLoggingWrapper.__init__(self, logging.DEBUG, limit=limit, verbose_return=verbose_return)

class vinfo(VerboseLazyLoggingWrapper):
    def __init__(self, limit=(), verbose_return=True):
        VerboseLazyLoggingWrapper.__init__(self, logging.INFO, limit=limit, verbose_return=verbose_return)

class vwarn(VerboseLazyLoggingWrapper):
    def __init__(self, limit=(), verbose_return=True):
        VerboseLazyLoggingWrapper.__init__(self, logging.WARN, limit=limit, verbose_return=verbose_return)

class verror(VerboseLazyLoggingWrapper):
    def __init__(self, limit=(), verbose_return=True):
        VerboseLazyLoggingWrapper.__init__(self, logging.ERROR, limit=limit, verbose_return=verbose_return)

class Base(object):
    """
    Inherit from this class to add better debug info.
    """

    def _debugrepr(self):
        if hasattr(self, 'to_json'):
            return self.to_json()
        encoded_attrs = ['"%s": %s' % (attr, debugrepr(getattr(self, attr))) \
                         for attr in self.__dict__]
        return '%s({%s})' % (self.__class__.__name__, ', '.join(encoded_attrs))
