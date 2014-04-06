
import inspect
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

class SourceContextFilter(logging.Filter):
    '''Allow us to override the lineno and filename in log messages with our wrappers'''
    def filter(self, record):
        if hasattr(record, 'override_filename'):
            record.filename = record.override_filename
        if hasattr(record, 'override_lineno'):
            record.lineno = record.override_lineno
        return True

def create_logger(handlers, level):
    """
    Build a new logger given an iterable of handlers
    """
    newlog = logging.getLogger('memdam')
    newlog.setLevel(level)
    for handler in newlog.handlers:
        newlog.removeHandler(handler)
    for handler in handlers:
        newlog.addHandler(handler)
    newlog.addFilter(SourceContextFilter())
    hack_logger(newlog)
    return newlog

#set up a default logger in case anything goes wrong before we've set up the real, multi-process
#logging
SIMPLE_LOGGER = create_logger([STDOUT_HANDLER], logging.WARN)
#TODO: this log variable should be replaced with something that automatically calls the right get_logger
_logger = SIMPLE_LOGGER
#note: just for pylint
_logger.trace = lambda x: None
hack_logger(_logger)
logging.addLevelName(TRACE, "TRACE")

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
            _logger.warn("Could not find email api key!")
config = Config()

def flush_logs():
    """Simply write all of the log events out of the queue, for debugging"""
    _logger.handlers[0].flush()

def shutdown_log():
    """Should be the very last statement in a program. Without this there are warnings about unclean debug client shutdowns."""
    _logger.handlers[0]._shutdown()

def is_threaded_logging_setup():
    return hasattr(_logger.handlers[0], 'queue')

#some debugging tools:

def debugrepr(obj, complete=True):
    """
    Converts any object into SOME reasonable kind of representation for debugging purposes.
    """
    if complete and hasattr(obj, '_debugrepr') and type(obj) != type:
        return obj._debugrepr()
    if isinstance(obj, buffer):
        return '(!raw bytes!)'
    if isinstance(obj, basestring):
        if len(obj) > 128:
            return obj[:64] + '...' + obj[-64:]
        return obj
    if hasattr(obj, '__len__'):
        if len(obj) > 4:
            ordered_obj = list(obj)
            to_serialize = ordered_obj[:2] + ['...'] + ordered_obj[-2:]
        else:
            to_serialize = obj
        return '[%s]' % (', '.join(debugrepr(inner) for inner in to_serialize))
    return repr(obj)

_created_loggers = {}
def _create_module_logger(module_name):
    if module_name == '__main__':
        module_name = 'memdam.__main__'
    if module_name not in _created_loggers:
        current_logger = logging.getLogger(module_name)
        hack_logger(current_logger)
        current_logger.addFilter(SourceContextFilter())
        _created_loggers[module_name] = current_logger
    return _created_loggers[module_name]

def log():
    '''
    Gross. We look at the module of the calling function, and use that to pull the right logger out.
    '''
    current_frame = sys._getframe()
    module = inspect.getmodule(current_frame.f_back)
    if module is None:
        module_name = '__main__'
    else:
        module_name = module.__name__
    return _create_module_logger(module_name)

class LazyLoggingWrapperBase(object):
    '''
    Decorator for logging call/arguments and return value from functions.

    Can specify the log level, and a list of arguments that should be listed verbosely.
    '''
    def __init__(self, level, verbose=(), verbose_return=False):
        self.verbose = verbose
        self.level = level
        self.verbose_return = verbose_return

    @staticmethod
    def special_self_encoding(data, is_verbose):
        return '%s[%s]' % (data.__class__.__name__, hex(id(data)))

    @staticmethod
    def encode_data(data, is_verbose):
        if is_verbose:
            return debugrepr(data)
        else:
            return repr(data)

    def get_verbose(self, func):
        return self.verbose

    def __call__(self, func):
        verbose_arg_names = self.get_verbose(func)

        all_names = func.func_code.co_varnames
        arg_names = tuple(all_names[:func.func_code.co_argcount])
        function_name = func.func_name
        extra = dict(override_filename=func.__code__.co_filename,
                     override_lineno=func.__code__.co_firstlineno+1)

        def get_log():
            module_name = func.__module__
            current_logger = _create_module_logger(module_name)
            if self.level == TRACE:
                log_func = current_logger.trace
            elif self.level == logging.DEBUG:
                log_func = current_logger.debug
            elif self.level == logging.INFO:
                log_func = current_logger.info
            elif self.level == logging.WARN:
                log_func = current_logger.warn
            elif self.level == logging.ERROR:
                log_func = current_logger.error
            else:
                raise Exception("Bad logging level for lazy logger: " + str(self.level))
            return log_func

        def make_param_string(*args, **kwargs):
            encoded_params = []
            keys_displayed = set()
            for i in range(0, min(len(args), len(arg_names))):
                arg_name = arg_names[i]
                keys_displayed.add(arg_name)
                if arg_name == 'self':
                    encoded_value = LazyLoggingWrapperBase.special_self_encoding(args[i], arg_name in verbose_arg_names)
                else:
                    encoded_value = LazyLoggingWrapperBase.encode_data(args[i], arg_name in verbose_arg_names)
                encoded_params.append('%s=%s' % (arg_name, encoded_value))
            for key in kwargs:
                if key not in keys_displayed:
                    encoded_value = LazyLoggingWrapperBase.encode_data(kwargs[key], key in verbose_arg_names)
                    encoded_params.append('%s=%s' % (key, encoded_value))
            if len(args) > len(arg_names):
                encoded_var_args = []
                varargs_name = inspect.getargspec(func).varargs
                for i in range(len(arg_names), len(args)):
                    encoded_value = LazyLoggingWrapperBase.encode_data(args[i], varargs_name in verbose_arg_names)
                    encoded_var_args.append(encoded_value)
                encoded_params.append('%s=%s' % (varargs_name, str(encoded_var_args)))
            return ', '.join(encoded_params)

        def make_error_string(e):
            return e.__class__.__name__ + ": " + str(e)

        def make_result_string(result):
            return LazyLoggingWrapperBase.encode_data(result, self.verbose_return)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log_func = get_log()
            log_func('%s -> (%s)' % (function_name, make_param_string(*args, **kwargs)), extra=extra)
            try:
                result = func(*args, **kwargs)
            except Exception, e:
                log_func('%s !! (%s)' % (function_name, make_error_string(e)), extra=extra)
                raise
            log_func('%s <- (%s)' % (function_name, make_result_string(result)), extra=extra)
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
