
import memdam

class Eventstore(memdam.Base):
    """
    An interface to the persistance services for storing ALL events.
    """

    def save(self, events):
        """
        Stores all events in the archive.
        Must be idempotent.
        :param events: a list of events to save
        :type  events: memdam.common.event.Event
        :raises: Exception if the events were not saved. Should simply retry later.
        """

    def get(self, event_id):
        """
        :param event_id: the UUID of the event to retrieve
        :type  event_id: UUID
        :returns: the event with that id
        :rtype:  memdam.common.event.Event
        :raises: Exception if there is no event with that id.
        """

    def find(self, query):
        """
        :param query: defines the filters which restrict which events should be found
        :type  query: memdam.common.query.Query
        :returns: all events that match the given query.
        :rtype: list(memdam.common.event.Event)
        """

    def delete(self, event_id):
        """
        Ensures that the given event id is deleted.
        Idempotent.

        :param event_id: the event id to be deleted.
        :type  event_id: uuid.UUID
        """
