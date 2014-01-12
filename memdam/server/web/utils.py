
import os
import flask

import memdam.blobstore.localfolder
import memdam.eventstore.sqlite
from memdam.server.web import app

def get_archive():
    """
    :returns: a new (or cached) archive
    :rtype: memdam.eventstore.api.Eventstore
    """
    archive = getattr(flask.g, '_archive', None)
    if archive is None:
        db_file = app.config['DATABASE_FOLDER']
        if db_file != ":memory:":
            if not os.path.exists(db_file):
                os.makedirs(db_file)
        archive = flask.g._archive = memdam.eventstore.sqlite.Eventstore(db_file)
    return archive

def get_blobstore():
    """
    :returns: a new (or cached) blobstore
    :rtype: memdam.blobstore.api.Blobstore
    """
    blobstore = getattr(flask.g, '_blobstore', None)
    if blobstore is None:
        base_folder = app.config['BLOBSTORE_FOLDER']
        blobstore = flask.g._blobstore = memdam.blobstore.localfolder.Blobstore(base_folder)
    return blobstore
