
# pylint: disable=E0611,W0611
from nose.tools import assert_raises, assert_equals

import memdam.common.timeutils
import memdam.common.event
import memdam.recorder.collector.collector
import memdam.recorder.eventqueue

DEVICE = "TempDevice"
SIMPLE_EVENTS = [\
    memdam.common.event.Event(memdam.common.timeutils.now(), "somedatatype", some__string="hello"),
    memdam.common.event.Event(memdam.common.timeutils.now(), "somedatatype", some_other__string="hello again")
]
#TODO: populate this and finish these tests
BINARY_EVENTS = []

def test_no_events():
    """Test processing when there are no events"""
    assert_equals(len(_base_test([])), 0)

def test_simple_events():
    """Test processing events when there are only simple events"""
    assert_equals(len(_base_test(SIMPLE_EVENTS)), len(SIMPLE_EVENTS))

def test_binary_events():
    """Test processing events when there are only binary events"""

def test_mixed_events():
    """Test processing events when there are both binary and simple events"""

def _base_test(events):
    """All tests run through this and just test different combinations of events"""
    class SimpleMailQueue(object):
        """Simple list of events"""
        def __init__(self):
            self.messages = []
        def add_message(self, message):
            """Add message to the list"""
            self.messages += [message]
    mail_queue = SimpleMailQueue()
    eventqueue = memdam.recorder.eventqueue.EventQueue(DEVICE, mail_queue)
    class SimpleCollector(memdam.recorder.collector.collector.Collector):
        """Just returns all of the events"""
        def collect(self):
            return events
    eventqueue.collect_events(SimpleCollector(None))
    eventqueue.process_events()
    return mail_queue.messages

if __name__ == '__main__':
    test_no_events()
    test_simple_events()
    test_binary_events()
    test_mixed_events()
