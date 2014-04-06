
import logging
import sys
import time

import nose.tools

import memdam
import memdam.common.parallel

def test_multithreaded_logging():
    """Check that logging works when using threads instead of processes"""
    with DebugProcessesAsThreads():
        _check_logging()

def test_multiprocess_logging():
    """Check that all log messages go to the parent thread correctly"""
    _check_logging()

def _check_logging():
    """Setup and run the test"""
    class MessageCountHandler(logging.StreamHandler):
        """For checking"""
        def __init__(self):
            logging.StreamHandler.__init__(self, sys.stdout)
            self.messages = []
        def emit(self, record):
            self.messages.append(record)
    message_counter = MessageCountHandler()
    handlers = [memdam.STDOUT_HANDLER, message_counter]
    memdam._logger = memdam.SIMPLE_LOGGER
    memdam.common.parallel.setup_log(level=logging.DEBUG, handlers=handlers)
    processes = []
    for i in range(5, 7):
        process = memdam.common.parallel.create_strand(
            name=str(i),
            target=_print_some_statements,
            args=(i,),
            use_process=True
            )
        process.start()
        processes += [process]
    _print_some_statements(8)
    for process in processes:
        process.join()
        nose.tools.eq_(process.exitcode, 0)
    time.sleep(2.0) #must wait for the logging thread to catch up
    nose.tools.eq_(len(message_counter.messages), 5+6+8)

def _print_some_statements(num):
    """Print some statements and exit"""
    for i in range(0, num):
        memdam.log().info("log " + str(i))
        time.sleep(0.3)

class DebugProcessesAsThreads(object):
    """Sets a global configuration variable that makes processes launch as threads instead"""

    def __init__(self):
        pass

    def __enter__(self):
        memdam.config.debug_processes = True
        return self

    def __exit__(self, ex_type, value, traceback):
        memdam.config.debug_processes = False

if __name__ == '__main__':
    test_multithreaded_logging()
    memdam.shutdown_log()
