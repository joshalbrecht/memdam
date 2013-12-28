
import uuid
import base64
import json

import requests

import memdam.common.event

class ServerError(Exception):
    """Raised if any error happens while talking to the server."""

class MemdamClient(object):
    """
    Abstract the HTTP transport layer.

    Retries must be handled by the consumer in the case of any ServerError.
    """
    def __init__(self, server_url, username, password):
        while server_url[-1] == '/':
            server_url = server_url[:-1]
        self._server_url = server_url
        self._request_kwargs = dict(
            headers={
                "Accept": "application/json",
                'Authorization': 'Basic ' + base64.b64encode(username + ":" + password)
            },
            #wait a few minutes before we conclude that the server is not responding
            timeout=180.0
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
        response = requests.get(self._server_url + "/events/" + event_id.hex, **self._request_kwargs)
        response.raise_for_status()
        return memdam.common.event.Event.from_json_dict(response.json())

    def save_event(self, event):
        """
        Set the data for a particular Event on the server.

        :param event: the Event to save
        :type  event: memdam.common.event.Event
        :raises: memdam.common.client.ServerError
        """
        new_event = self._save_files_in_event(event)
        event_json = json.dumps(new_event.to_json_dict())
        response = requests.put(self._server_url + "/events/" + new_event.id__id.hex, data=event_json, **self._request_kwargs)
        response.raise_for_status()

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
        query_json = json.dumps(query.to_json_dict())
        response = requests.put(self._server_url + "/queries", data=query_json, **self._request_kwargs)
        response.raise_for_status()
        event_json_list = response.json()
        event_list = [memdam.common.event.Event.from_json_dict(x) for x in event_json_list]
        return event_list

    def _save_files_in_event(self, event):
        """
        Convert any Event into one that ONLY has files on the server where we are about to create
        this Event by sending each of the files as blobs to the server.

        :param event: the event in which to look for files
        :type  event: memdam.common.event.Event
        :returns: a new Event, with the same id, and all __file attributes pointing to paths on
            self._server_url
        :rtype: memdam.common.event.Event
        """
        new_event_dict = {}
        for key in event.keys:
            value = event.get_field(key)
            if memdam.common.event.Event.field_type(key) == memdam.common.event.FieldType.FILE:
                if not value.startswith(self._server_url):
                    value = self._save_file(value)
            new_event_dict[key] = value
        return memdam.common.event.Event.from_keys_dict(new_event_dict)

    def _save_file(self, url):
        """
        Uploads a file from the provided path and returns the new path.

        :param url: the path to the data. Should be a URL. For now only the file:// scheme is supported.
        :type  url: string
        :returns: the new path. Will be a URL.
        :rtype: string
        """
        assert url.startswith("file://")
        path = url[:len("file://")]
        files = {'file': open(path, 'rb')}
        blob_id = uuid.uuid4()
        extension = path.split('.')[-1].lower()
        assert len(extension) == 3, "files should end in a 3 letter extension, for sanity"
        new_url = self._server_url + "/blobs/" + blob_id + "." + extension
        response = requests.post(new_url, files=files)
        response.raise_for_status()
        return new_url
