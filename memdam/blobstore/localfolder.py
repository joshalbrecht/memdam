
import shutil
import os

import memdam.blobstore.api

class Blobstore(memdam.blobstore.api.Blobstore):
    """
    Just a simple place to dump files. Uses a particular folder on local storage.
    """

    def __init__(self, folder):
        self._folder = folder

    def set_data_from_file(self, blob_id, extension, input_path):
        path = self._get_path(blob_id, extension)
        _make_folders(path)
        shutil.copyfile(input_path, path)

    def get_data_to_file(self, blob_id, extension, output_path):
        path = self._get_path(blob_id, extension)
        shutil.copyfile(path, output_path)

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
    level_two_folder, _ = os.path.split(path)
    level_one_folder, _ = os.path.split(level_two_folder)
    if not os.path.exists(level_one_folder):
        os.mkdir(level_one_folder)
    if not os.path.exists(level_two_folder):
        os.mkdir(level_two_folder)
