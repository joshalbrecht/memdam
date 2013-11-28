
class ArchiveInterface(object):
    """
    An interface to the persistance services for storing ALL events.
    """

    def save(self, events):
        """
        Stores all events in the archive.
        Must be idempotent.
        Remember that no two events can have the same time--if you insert two with the same time,
        the later will overwrite the former.
        :param events: a list of events to save
        :type  events: memdam.common.event.Event
        :raises: Exception if the events were not saved. Should simply retry later.
        """

    def find(self, query=None):
        """
        :returns: all events that match the given query.
        :rtype: list(memdam.common.event.Event)
        """
