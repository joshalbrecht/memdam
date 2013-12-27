
import os

class Blobstore(object):
    """
    Just a simple place to dump files
    """

    def __init__(self, folder):
        self._folder = folder

    def get_path(self, blob_id, extension):
        """
        :returns: the absolute path to where this data should be located
        :rtype: string
        """
        return os.path.join(self._folder, blob_id + '.' + extension)

    def set_from_flask(self, blob_id, extension, uploaded_file):
        """
        Save a file that was uploaded to flask
        """
        path = self.get_path(blob_id, extension)
        uploaded_file.save(path)

    def set_raw(self, blob_id, extension, raw_data):
        """
        Save a file based on the raw data
        """
        path = self.get_path(blob_id, extension)
        with open(path, "wb") as out_file:
            out_file.write(raw_data)
