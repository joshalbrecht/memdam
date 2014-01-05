
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

    def set_data_from_file(self, blob_id, extension, input_path):
        files = {'file': open(input_path, 'rb')}
        extension = input_path.split('.')[-1].lower()
        new_url = "/blobs/" + blob_id.hex + "." + extension
        self._client.request("PUT", new_url, files=files, headers={'Content-Type': None})
        return self.get_url_prefix() + blob_id.hex + "." + extension

    def get_data_to_file(self, blob_id, extension, output_path):
        new_url = "/blobs/" + blob_id.hex + "." + extension
        response = self._client.request("GET", new_url, headers={'Accept': None, 'Content-Type': None})
        with open(output_path, 'wb') as outfile:
            outfile.write(response.content)

    def delete(self, blob_id, extension):
        url = "/blobs/" + blob_id.hex + "." + extension
        self._client.request("DELETE", url)
