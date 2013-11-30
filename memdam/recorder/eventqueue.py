
import Queue

from fn import _
from fn.uniform import *
from fn.monad import Option

import memdam.recorder.message

#TODO: actually make the event queue persistent (possibly by using sqlite) (postpone this for now)
class EventQueue(object):
    """
    Receives events from Collectors.
    Turns the events into email messages and inserts them into the MailQueue.
    """
    def __init__(self, device, mail_queue):
        self._device = device
        self._mail_queue = mail_queue
        self._events = Queue.Queue()

    def collect_events(self, collector):
        """
        Scheduled periodically as defined in the configuration.
        Adds events to the event queue.
        """
        for event in collector.collect():
            self._events.put(event)

    def process_events(self):
        """
        Scheduled periodically.
        Pulls all of the events out of the queue and makes messages out of them and inserts those messages into the mail queue.
        Runs in its own thread (may take a while to split files for example)
        Should take a temporary lock out on the queue while pulling messages out, but NOT retain the lock while splitting a large event.
        The queue is not persistent.
        When shutting down, call this.
        Should empty the queue on each invocation, even if that takes a while.
        """

        #pull all events out of the queue
        events = []
        try:
            while True:
                events.append(self._events.get_nowait())
        except Queue.Empty:
            pass

        #turn each binary event into a message
        binary_events = list(filter(lambda x: x.has_file(), events))
        binary_messages = list(map(self._create_binary_message, binary_events))

        #add other events to a single message
        simple_events = list(filter(lambda x: not x.has_file(), events))
        simple_message = Option.from_value(simple_events or None)\
            .map(lambda x: [self._create_simple_message(x)])

        #mail the messages
        messages = simple_message.get_or([]) + binary_messages
        for message in messages:
            self._mail_queue.add_message(message)

    def _create_simple_message(self, events):
        """
        Create a message with a json array for all events
        """
        message = memdam.recorder.message.Message(self._device, events)
        return message

    def _create_binary_message(self, event):
        """
        Turn an Event with some binary content into a list of Message's (1, or many if the file is
        too large)
        """
        #TODO: split large attached files into multiple messages
        return []
