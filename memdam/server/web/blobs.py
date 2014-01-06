
import uuid
import re
import os
import base64

import flask

import memdam.common.utils
import memdam.common.blob
import memdam.common.validation
import memdam.server.web.errors
import memdam.server.web.utils
import memdam.server.web.auth

blueprint = flask.Blueprint('blobs', __name__)

@blueprint.route('/<unsafe_blob_id>.<unsafe_extension>', methods = ['GET', 'PUT', 'DELETE'])
@memdam.server.web.auth.requires_auth
def blobs(unsafe_blob_id, unsafe_extension):
    """
    Get/set blobs based on unique ids
    """
    blob_id = validate_uuid(unsafe_blob_id)
    extension = validate_extension(unsafe_extension)
    blob_ref = memdam.common.blob.BlobReference(blob_id, extension)
    filename = memdam.common.utils.make_temp_path()
    if flask.request.method == 'PUT':
        if 'multipart/form-data' in flask.request.content_type:
            if not len(flask.request.files) == 1:
                raise memdam.server.web.errors.BadRequest("Must only upload one file at a time")
            uploaded_file = flask.request.files.values()[0]
            uploaded_file.save(filename)
        elif flask.request.json:
            if not 'data' in flask.request.json:
                raise memdam.server.web.errors.BadRequest("Must base64 encode the data into the 'data' key")
            raw_data = base64.b64decode(flask.request.json['data'])
            with open(filename, "wb") as out_file:
                out_file.write(raw_data)
        else:
            raise memdam.server.web.errors.BadRequest("Must use json or multipart/form-data upload methods")
        memdam.server.web.utils.get_blobstore().set_data_from_file(blob_ref, filename)
        os.remove(filename)
        return '', 204
    elif flask.request.method == 'DELETE':
        memdam.server.web.utils.get_blobstore().delete(blob_ref)
        return '', 204
    else:
        memdam.server.web.utils.get_blobstore().get_data_to_file(blob_ref, filename)
        with FileResponseCleaner(filename):
            return flask.send_file(filename)

def validate_uuid(unsafe_blob_id):
    """
    :param unsafe_blob_id: input from the user that should represent a uuid (hex encoded)
    :type  unsafe_blob_id: string
    :returns: the UUID that is referred to
    :rtype: uuid.UUID
    :raises: memdam.server.web.errors.BadRequest (if the input is not valid)
    """
    if not re.compile("^" + memdam.common.validation.UUID_HEX_PATTERN + "$", re.IGNORECASE).match(unsafe_blob_id):
        raise memdam.server.web.errors.BadRequest("blob id should consist of only hex characters")
    if len(unsafe_blob_id) != 32:
        raise memdam.server.web.errors.BadRequest("blob id should have exactly 32 characters")
    blob_id = unsafe_blob_id.lower()
    return uuid.UUID(blob_id)

def validate_extension(unsafe_extension):
    """
    :param unsafe_extension: input from the user that should represent a valid file extension
    :type  unsafe_extension: string
    :returns: the (possibly cleaned) file extension
    :rtype: string
    :raises: memdam.server.web.errors.BadRequest (if the input is not valid)
    """
    if not re.compile("^" + memdam.common.validation.EXTENSION_PATTERN + "$", re.IGNORECASE).match(unsafe_extension):
        raise memdam.server.web.errors.BadRequest("extension should consist of only characters a-z and 0-9")
    return unsafe_extension.lower()

class FileResponseCleaner(object):
    """Simply deletes the file when the context"""
    def __init__(self, filename):
        self.filename = filename
    def __enter__(self):
        pass
    def __exit__(self, extype, value, traceback):
        os.remove(self.filename)
