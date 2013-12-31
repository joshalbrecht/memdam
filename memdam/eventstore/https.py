
import json

import memdam.eventstore.api

class Eventstore(memdam.eventstore.api.Eventstore):
    """
    Remote access (via HTTPS REST API) to the Eventstore interface.

    :attr _client: the method for actually making calls to the remote server
    :type _client: memdam.common.client.MemdamClient
    """

    def __init__(self, client):
        self._client = client

    def save(self, events):
        """
        Stores all events in the archive.
        Must be idempotent.
        :param events: a list of events to save
        :type  events: memdam.common.event.Event
        :raises: Exception if the events were not saved. Should simply retry later.
        """
        for event in events:
            event_json = json.dumps(event.to_json_dict())
            self._client.request('PUT', "/events/" + event.id__id.hex, data=event_json)

    def get(self, event_id):
        """
        :param event_id: the UUID of the event to retrieve
        :type  event_id: UUID
        :returns: the event with that id
        :rtype:  memdam.common.event.Event
        :raises: Exception if there is no event with that id.
        """
        response = self._client.request('GET', "/events/" + event_id.hex)
        return memdam.common.event.Event.from_json_dict(response.json())

    def find(self, query=None):
        """
        :returns: all events that match the given query.
        :rtype: list(memdam.common.event.Event)
        """
        query_json = json.dumps(query.to_json_dict())
        response = self._client.request('POST', "/queries", data=query_json)
        event_json_list = response.json()
        event_list = [memdam.common.event.Event.from_json_dict(x) for x in event_json_list]
        return event_list
