
class Blobstore(object):
    """
    Interface for file storage
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
