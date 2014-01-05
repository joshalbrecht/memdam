
import shutil
import os

import memdam.blobstore.api

class Blobstore(memdam.blobstore.api.Blobstore):
    """
    Just a simple place to dump files. Uses a particular folder on local storage.
    """

    def __init__(self, folder):
        folder = os.path.abspath(folder)
        while folder[-1] == '/':
            folder = folder[:-1]
        self._folder = folder + '/'

    def get_url_prefix(self):
        return "file://" + self._folder

    def set_data_from_file(self, blob_id, extension, input_path):
        path = self._get_path(blob_id, extension)
        _make_folders(path)
        shutil.copyfile(input_path, path)
        return self.get_url_prefix() + blob_id.hex + "." + extension

    def get_data_to_file(self, blob_id, extension, output_path):
        path = self._get_path(blob_id, extension)
        if not os.path.exists(path):
            raise memdam.blobstore.api.MissingBlob()
        shutil.copyfile(path, output_path)

    def delete(self, blob_id, extension):
        path = self._get_path(blob_id, extension)
        try:
            os.remove(path)
        except OSError, e:
            #don't care what happened as long as the file no longer exists
            if not os.path.exists(path):
                return
            raise e


    def exists(self, blob_id, extension):
        return os.path.exists(self._get_path(blob_id, extension))

    def _get_path(self, blob_id, extension):
        """
        Use this to figure out where data is/should be stored for a blob.

        All blobs are NOT stored in the same folder because that would be too many files in a single
        folder for most filesystems. Instead, we simply create two levels of folders before storing
        the blob, so that it works like this:

        a1b2dde36185fab.ext -> /base/folder/a1/b2/dde36185fab.ext

        :param blob_id: the unique identifier for the blob
        :type  blob_id: uuid.UUID
        :param extension: a lowercase file extension
        :type  extension: string
        :returns: the absolute path to where this data should be located
        :rtype: string
        """
        hex_blob_id = blob_id.hex
        mangled_blob_id = os.path.join(hex_blob_id[:2], hex_blob_id[2:4], hex_blob_id[4:])
        return os.path.join(self._folder, mangled_blob_id + '.' + extension)

def _make_folders(path):
    """Create the subfolders in our directory"""
    folder, _ = os.path.split(path)
    try:
        os.makedirs(folder)
    except OSError, e:
        #don't care what happened as long as the folder exists
        if os.path.exists(folder):
            return
        raise e
