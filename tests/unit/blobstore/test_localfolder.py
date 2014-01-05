
import uuid
import os
import shutil

import memdam.common.utils
import memdam.blobstore.localfolder

def test_blobstore():
    """Check that the blobstore works as expected."""
    temp_folder = memdam.common.utils.make_temp_path()
    os.mkdir(temp_folder)
    blobstore = memdam.blobstore.localfolder.Blobstore(temp_folder)
    temp_in_file = memdam.common.utils.make_temp_path()
    file_data = 'some\ndata'
    with open(temp_in_file, 'wb') as outfile:
        outfile.write(file_data)
    blob_id = uuid.uuid4()
    extension = "txt"
    blobstore.set_data_from_file(blob_id, extension, temp_in_file)
    temp_out_file = memdam.common.utils.make_temp_path()
    blobstore.get_data_to_file(blob_id, extension, temp_out_file)
    with open(temp_out_file, 'rb') as infile:
        assert infile.read() == file_data
    os.remove(temp_in_file)
    os.remove(temp_out_file)
    shutil.rmtree(temp_folder)
