
import memdam.recorder.collector.collector

class GmailCollector(memdam.recorder.collector.collector.Collector):
    """
    Collects the following information types from gmail:

    com.memdam.social.communication.email
    com.memdam.social.communication.im
    com.memdam.social.people.contact

    Works on its own schedule.
    Runs a controller thread that periodically collects unique email ids and message ids from gmail,
    and some worker threads for working through the new messages.
    """

    def __init__(self, config, state_store):
        memdam.recorder.collector.collector.Collector.__init__(self, config, state_store)

    def start(self):
        #start a controller thread with a reference to the queue into which email ids should be inserted
        #workers simply pull unique ids from here, and insert events into the queue (along with the unique id)
        pass

    def collect(self):
        #simply empty the queue and return those events
        #remember the unique ids to be persisted in our state_store when post_collect is called
        pass

    def post_collect(self):
        #when events are pulled out of the thread, those unique ids should be marked as handled
        #note: this should be persisted only after the events have been pulled out and persisted into the event queue
        #which has to happen in a post_collect call
        #general rule: prefer duplicate insertion of the same event where possible, since the insertion itself is idempotent and it should be exactly the same
        pass

    def stop(self):
        #cleanly shutdown the thread and workers
        #workers with PoisonPill, main thread with a please and thank you ;)
        #after everything is done, deal with the queue (probably have to empty and shutdown)
        pass
