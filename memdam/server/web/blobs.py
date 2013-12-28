
import os
import base64

import flask

import memdam.server.web.utils
import memdam.server.web.auth

blueprint = flask.Blueprint('blobs', __name__)

#TODO: input validation
@blueprint.route('/<blob_id>.<extension>', methods = ['GET', 'PUT'])
@memdam.server.web.auth.requires_auth
def blobs(blob_id, extension):
    """
    Get/set blobs based on unique ids
    """
    if flask.request.method == 'PUT':
        if flask.request.json:
            if not 'data' in flask.request.json:
                #TODO: change to other error format
                flask.abort(401, "Must base64 encode the data into the 'data' key")
            raw_data = base64.b64decode(flask.request.json['data'])
            memdam.server.web.utils.get_blobstore().set_raw(blob_id, extension, raw_data)
        elif flask.request.content_type == 'multipart/form-data':
            if not len(flask.request.files) == 1:
                flask.abort(401, "Must only upload one file at a time")
            uploaded_file = flask.request.files.values()[0]
            memdam.server.web.utils.get_blobstore().set_from_flask(blob_id, extension, uploaded_file)
        else:
            flask.abort(401, "Must use json or multipart/form-data upload methods")
        return '', 204
    else:
        filename = memdam.server.web.utils.make_temp_path()
        memdam.server.web.utils.get_blobstore().get_data_to_file(blob_id, extension, filename)
        with FileResponseCleaner(filename):
            return flask.send_file(filename)

class FileResponseCleaner(object):
    """Simply deletes the file when the context"""
    def __init__(self, filename):
        self.filename = filename
    def __enter__(self):
        pass
    def __exit__(self, extype, value, traceback):
        os.remove(self.filename)
