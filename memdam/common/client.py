
import json

import unirest

import memdam.common.event

#TODO: probably a bad idea, but file uploads are going to take a forever.
#TODO: change to using python requests instead, way better looking library
unirest.timeout(None)

class ServerError(Exception):
    """Raised if any error happens while talking to the server."""

class MemdamClient(object):
    """
    Abstract the HTTP transport layer.

    Retries must be handled by the consumer in the case of any ServerError.
    """
    def __init__(self, server_url, username, password):
        self._server_url = server_url
        self._username = username
        self._password = password
        self._unirest_kwargs = dict(
            headers={ "Accept": "application/json" },
            auth=(self._username, self._password)
        )

    def load_event(self, event_id):
        """
        Get all data for an Event from the server.

        :param event_id: the unique identifier for the event
        :type  event_id: uuid.UUID
        :returns: the event with that unique identifier
        :rtype: memdam.common.event.Event
        :raises: memdam.common.client.ServerError
        """
        response = unirest.get(self._server_url + "/events/" + event_id.hex, **self._unirest_kwargs)
        if response.code - 200 >= 100:
            raise ServerError("Request to server failed: %s %s" % (response.code, response.raw_body))
        return memdam.common.event.Event.from_json_dict(response.body)

    def save_event(self, event):
        """
        Set the data for a particular Event on the server.

        :param event: the Event to save
        :type  event: memdam.common.event.Event
        :raises: memdam.common.client.ServerError
        """
        #TODO: save each of the files separately first and create a modified event
        event_json = json.dumps(event.to_json_dict())
        response = unirest.put(self._server_url + "/events/" + event.id__id.hex, params=event_json, **self._unirest_kwargs)
        if response.code - 200 >= 100:
            raise ServerError("Request to server failed: %s %s" % (response.code, response.raw_body))

    def find_events(self, query):
        """
        Returns all Events that match the given Query

        :param query: A set of filters to apply to all Events on the server
        :type  query: memdam.common.query.Query
        :returns: a list of Events defined by the filters in the query.
            Note that this list may be gigantic.
        :rtype: list(memdam.common.event.Event)
        :raises: memdam.common.client.ServerError
        """
