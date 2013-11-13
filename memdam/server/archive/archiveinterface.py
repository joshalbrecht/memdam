
class ArchiveInterface(object):
    """
    An interface to the persistance services for storing ALL events.
    """

    def save(self, events):
        """
        Must be idempotent.
        :param events: a list of events to save
        :type  events: memdam.common.event.Event
        :raises: Exception if the events were not saved. Should simply retry later.
        """
