
import types
import copy
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
                'Content-Type': 'application/json',
                "Accept": "application/json",
                'Authorization': 'Basic ' + base64.b64encode(username + ":" + password)
            },
            #wait a few minutes before we conclude that the server is not responding
            timeout=180.0
        )

    def request(self, method, url, **kwargs):
        """
        Make a request to the remote server. Merges any kwargs into our default kwargs, so that
        headers, auth, etc are all taken care of, but can be overriden.

        :param method: the name of the method (GET, POST, PUT, etc)
        :type  method: string
        :param url: path on the server to make the request to
        :type  url: string
        :param kwargs: see requests.post for full description of all keyword args
        :type  kwargs: dict
        :returns: the response from the server
        :rtype: ??? (something from requests library)
        """
        merged_kwargs = _merge(kwargs, copy.deepcopy(self._request_kwargs))
        new_url = self._server_url + url
        request_method = getattr(requests, method.lower())
        response = request_method(new_url, **merged_kwargs)
        _validate_response(response)
        return response

#TODO: replace this with the python function that does it, I forgot the name
def _merge(dest, source):
    """
    Recursively deep copy things from source to dest dicts.
    The key will be deleted if mapped to None
    """
    for key in source:
        if source[key] == None:
            if key in dest:
                del dest[key]
            continue
        if key in dest:
            if isinstance(dest[key], types.DictType):
                dest[key] = _merge(dest[key], source.get(key, {}))
            else:
                dest[key] = source[key]
        else:
            dest[key] = copy.deepcopy(source[key])
    return dest

def _validate_response(response):
    try:
        response.raise_for_status()
    except requests.RequestException, e:
        try:
            extra_data = response.json()
        except Exception:
            raise e
        raise MemdamSpecificError(extra_data)

class MemdamSpecificError(requests.RequestException):
    """Subclassing requests error type to provide extra info when available"""
    def __init__(self, data):
        requests.RequestException.__init__(self)
        self.data = data

    def __str__(self):
        return "Request failed: " + str(self.data)
