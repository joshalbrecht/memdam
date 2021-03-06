
import re
import types

import nose.tools

import memdam
import memdam.common.utils

_original_handle_function = None
_log_call_count = 0
def mock_log():
    """
    change wrap memdam.log.trace so that we can count the number of calls
    """
    global _original_handle_function
    _original_handle_function = memdam._logger.handlers[0].handle
    def new_handle(self, *args, **kwargs):
        global _log_call_count
        _log_call_count += 1
        _original_handle_function(*args, **kwargs)
    memdam._logger.handlers[0].handle = types.MethodType(new_handle, memdam._logger.handlers[0].handle)

def clear_log():
    """
    unwrap memdam.log.trace so that it is back to normal for other tests
    """
    global _original_handle_function, _log_call_count
    _log_call_count = 0
    memdam._logger.handlers[0].handle = _original_handle_function

def setup():
    """
    global setup. everything should run at the trace level
    """
    memdam._logger.setLevel(memdam.TRACE)

@memdam.vtrace()
def function_to_call(thing):
    value_class = ArbitraryClassWithFunctionsAndData(1, 2)
    class_to_call = ArbitraryClassWithFunctionsAndData(None, value_class)
    return class_to_call.some_function("a", "b", kwarg2=re.compile("great regex"))

class SpecialException(Exception): pass

class ArbitraryClassWithFunctionsAndData(memdam.Base):

    def __init__(self, val1, val2):
        self.val1 = val1
        self.val2 = val2

    @memdam.vtrace()
    def some_function(self, thing, other_thing, kwarg1=None, kwarg2=4, *args):
        self.do_stuff(other_thing)
        return 4

    @memdam.vtrace()
    def do_stuff(self, other_thing):
        return "inner return value string thingy"

    @memdam.vtrace()
    def uh_oh(self, data):
        raise SpecialException("Data is too data-y: " + str(data))

@nose.tools.with_setup(mock_log, clear_log)
def test_tracing():
    function_to_call([ArbitraryClassWithFunctionsAndData(4, 4), ArbitraryClassWithFunctionsAndData(4, 4), 1, 1, 1, 1, 2, 2, "suuuuuupppperlonnnngggstrrriinngggg" * 400])
    nose.tools.eq_(_log_call_count, 6)

@nose.tools.with_setup(mock_log, clear_log)
def test_exception_tracing():
    try:
        ArbitraryClassWithFunctionsAndData("x", 234876).uh_oh("some more data")
    except SpecialException:
        nose.tools.eq_(_log_call_count, 2)
    else:
        raise Exception("Was supposed to raise a SpecialException!")

if __name__ == '__main__':
    setup()

    mock_log()
    test_tracing()
    clear_log()

    mock_log()
    test_exception_tracing()
    clear_log()
