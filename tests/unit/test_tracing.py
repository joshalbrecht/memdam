
import tempfile
import re
import types
import os
import sys

import nose.tools

import memdam
import memdam.common.utils

_original_trace_function = None
_trace_call_count = 0
def mock_log():
    """
    change wrap memdam.log.trace so that we can count the number of calls
    """
    global _original_trace_function
    _original_trace_function = memdam.log.trace
    def new_trace(self, *args, **kwargs):
        global _trace_call_count
        _trace_call_count += 1
        _original_trace_function(*args, **kwargs)
    memdam.log.trace = types.MethodType(new_trace, memdam.log)

def clear_log():
    """
    unwrap memdam.log.trace so that it is back to normal for other tests
    """
    global _original_trace_function, _trace_call_count
    _trace_call_count = 0
    memdam.log = _original_trace_function

_TRACE_FILE_NAME = memdam.common.utils.make_temp_path()

def setup():
    """
    global setup. everything should run at the trace level
    """
    memdam.log.setLevel(memdam.TRACE)

def teardown():
    """
    run at the end of the module to clean up the temp file
    """
    os.remove(_TRACE_FILE_NAME)

def setup_tracer_test(regexes=(".*memdam.*",)):
    """
    mocks the log.trace function and manipulates sys.argv to use a file with the regexes that were passed in
    """
    mock_log()
    with open(_TRACE_FILE_NAME, 'wb') as outfile:
        outfile.writelines(regexes)
    memdam._TRACE_EXPRESSIONS = None
    memdam._TRACE_MATCHES = {}
    sys.argv = sys.argv + ['--trace-file=' + _TRACE_FILE_NAME]

def teardown_tracer_test():
    """
    resets log.trace function and fixes sys.argv and other global state
    """
    clear_log()
    memdam._TRACE_EXPRESSIONS = None
    memdam._TRACE_MATCHES = {}
    sys.argv = sys.argv[-1:]

@memdam.tracer
def function_to_call(thing):
    value_class = ArbitraryClassWithFunctionsAndData(1, 2)
    class_to_call = ArbitraryClassWithFunctionsAndData(None, value_class)
    return class_to_call.some_function("a", "b", kwarg2=re.compile("great regex"))

class SpecialException(Exception): pass

class ArbitraryClassWithFunctionsAndData(memdam.Base):
    def __init__(self, val1, val2):
        self.val1 = val1
        self.val2 = val2

    def some_function(self, thing, other_thing, kwarg1=None, kwarg2=4):
        self.do_stuff(other_thing)
        return 4

    def do_stuff(self, other_thing):
        return "inner return value string thingy"

    def uh_oh(self, data):
        raise SpecialException("Data is too data-y: " + str(data))

@nose.tools.with_setup(setup_tracer_test, teardown_tracer_test)
def test_tracing():
    function_to_call([ArbitraryClassWithFunctionsAndData(4, 4), ArbitraryClassWithFunctionsAndData(4, 4), 1, 1, 1, 1, 2, 2, "suuuuuupppperlonnnngggstrrriinngggg" * 400])
    nose.tools.eq_(_trace_call_count, 14)

@nose.tools.with_setup(setup_tracer_test, teardown_tracer_test)
@nose.tools.raises(SpecialException)
def test_exception_tracing():
    ArbitraryClassWithFunctionsAndData("x", 234876).uh_oh("some more data")

#TODO: test that the logic for applying to only particular files/modules works
#might want to consume the sys.argv that we use so I don't have to modify the mains...
def test_specific_module_tracing():
    pass

if __name__ == '__main__':
    setup()

    setup_tracer_test()
    test_tracing()
    teardown_tracer_test()

    setup_tracer_test()
    try:
        test_exception_tracing()
    except SpecialException:
        pass
    else:
        raise Exception("was supposed to fail previously!")
    teardown_tracer_test()

    teardown()

