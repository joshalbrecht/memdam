
class Blobstore(object):
    """
    Interface for file storage
    """

    def get_url_prefix(self):
        """
        :returns: the prefix for urls to access a given blob and extension
        (ex: http://somewhere.com/blobs/)
        :rtype: string
        """

    def set_data_from_file(self, blob_id, extension, input_path):
        """
        Save a file based on the raw data.

        :param blob_id: the unique identifier for the blob
        :type  blob_id: uuid.UUID
        :param extension: a lowercase file extension
        :type  extension: string
        :param output_path: path with the data that should be written
        :type  output_path: string
        :returns: the url associated with this file
        :rtype: string
        """

    def get_data_to_file(self, blob_id, extension, output_path):
        """
        Saves the raw data to a file of your choosing. You are responsible for making sure it gets
        deleted when you're done with it.

        :param blob_id: the unique identifier for the blob
        :type  blob_id: uuid.UUID
        :param extension: a lowercase file extension
        :type  extension: string
        :param output_path: where the data should be written
        :type  output_path: string
        """

    def delete(self, blob_id, extension):
        """
        Ensure that the file with this blob id and extension is removed.
        Idempotent.

        :param blob_id: the unique identifier for the blob
        :type  blob_id: uuid.UUID
        :param extension: a lowercase file extension
        :type  extension: string
        """
