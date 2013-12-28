
import memdam.server.blobstore

def test_blobstore():
    """Check that the blobstore works as expected."""
    blobstore = memdam.server.blobstore.Blobstore(temp_folder)
    blobstore.set_raw(blob_id, extension, data)
    #TODO: change blobstore interface to not expose path.
    #maybe then we can make an alternative implementation that stores the binaries encrypted in S3 instead
    #or at any other location. Then it would be much easier to move around the event storage, which is much smaller
    #
    #perhaps change to get(id, ext, dest_path)
    #and then just clean up usually
    #then we can store anywhere
    #
    #in the future, could even store in glacier (though we'd need a bit of customness to pull out the right binaries)
    blobstore.get_path(blob_id, extension)
