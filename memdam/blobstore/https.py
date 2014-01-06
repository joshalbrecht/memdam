
import requests

import memdam.blobstore.api

class Blobstore(memdam.blobstore.api.Blobstore):
    """
    Save and load files from a remote server via our HTTPS REST API.

    :attr _client: the method for actually making calls to the remote server
    :type _client: memdam.common.client.MemdamClient
    """

    def __init__(self, client):
        self._client = client

    def get_url_prefix(self):
        return self._client.get_base_url() + "/blobs/"

    def set_data_from_file(self, blob_ref, input_path):
        files = {'file': open(input_path, 'rb')}
        new_url = "/blobs/" + blob_ref.name
        self._client.request("PUT", new_url, files=files, headers={'Content-Type': None})

    def get_data_to_file(self, blob_ref, output_path):
        new_url = "/blobs/" + blob_ref.name
        response = self._client.request("GET", new_url, headers={'Accept': None, 'Content-Type': None})
        with open(output_path, 'wb') as outfile:
            outfile.write(response.content)

    def delete(self, blob_ref):
        url = "/blobs/" + blob_ref.name
        self._client.request("DELETE", url)

    #TODO: lol this is inefficient. Requests the entire file. Should make something less stupid.
    def exists(self, blob_ref):
        new_url = "/blobs/" + blob_ref.name
        try:
            self._client.request("GET", new_url, headers={'Accept': None, 'Content-Type': None})
        except requests.RequestException:
            return False
        return True
