
import memdam.recorder.collector.uniqueidcollector

def _collector(queue, finished=None, username=None, password=None):
    """
    Called periodically to collect all new unique ids.
    """
    #TODO: actually, this kinda sucks, since we'll be adding these ids to a list that potentially already has them
    #eg, mismatch between initial "state" (which is actually only even loaded once) and the remote state
    #even worse when we consider things where ids shift (imap with multiple users? files?)
    #maybe need a unique queue...
    #problems:
    #1. on each call, will insert all differences between ORIGINAL state and current remote state
    #2. on each call, will insert all differences, with no consideration of those ids that were already queued
    #3. some services have unstable ids (example, imap where emails can be deleted and then the ids shift?)
    #
    #how about this:
    #we pass in a list/set of all of the things either seen so far, or in the queue already
    #this function just lets us know about anything that we're missing and returns that set
    #the caller merges the two, and provides the merged set next time
    #hmm, except that if there are unstable sets, the set of things we've seen so far will grow in an unbounded fashion
    #and since that is persisted to json, then we're screwed again :(
    #also, the processor function below needs to gracefully handle failures
    #eg, in this case, by backing off
    #but more generally should expect failure, especially if ids shift or may no longer be valid
    #in the case of imap specifically, ids are unique PER FOLDER (weird)
    #in the case of gmail specifically, there is a unique message id that can be used sensibly (unsure if chats are included)
    #
    #I guess file system events should NOT be a UniqueIdCollector--the collection can grow forever, and we don't really care
    #I guess really it needs two different ones--historical file collector (which IS a uniqueid collector)
    #  bleh, except that we still get the growing ness with temp files
    #ahh, nah, historical is a date ordered one (just collects things in order of date and stores the most recent date)
    #
    #email could ALMOST be this way (as ids just increase, sort of an OrderedIdCollector) except that gmail doesn't guarantee those semantics necessarily...
    #...or maybe it does? that would certainly be simpler...
    #
    #ok, so meta note--implementors should prefer collectors in the order:
    #sampling
    #ordered id
    #unique id
    #
    #and full filesystem backup collector can work with ext4 and snapshots (or that other one)
    #ordered ids then are snapshotid-alphabetical_path

class GmailCollector(memdam.recorder.collector.uniqueidcollector.UniqueIdCollector):
    """
    Collects the following information types from gmail:

    com.memdam.social.communication.email
    com.memdam.social.communication.im
    com.memdam.social.people.contact
    """

    def __init__(self, config, state_store):
        memdam.recorder.collector.uniqueidcollector.UniqueIdCollector.__init__(
            self,
            config,
            state_store
        )

    def start(self):
        memdam.recorder.collector.uniqueidcollector.UniqueIdCollector.launch(
            self,
            _collector,
            {
                'finished': set(self._state_store.get_state()['finished']),
                'username': username,
                'password': password,
            },
            processor,
            processor_kwargs
        )
