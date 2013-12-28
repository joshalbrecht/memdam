
import tempfile

import flask

import memdam.server.blobstore
import memdam.server.archive.sqlite
from memdam.server.web import app

def get_archive():
    """
    :returns: a new (or cached) archive
    :rtype: memdam.server.archive.archiveinterface.ArchiveInterface
    """
    archive = getattr(flask.g, '_archive', None)
    if archive is None:
        db_file = app.config['DATABASE']
        blob_url = app.config['BLOB_URL']
        archive = flask.g._archive = memdam.server.archive.sqlite.SqliteArchive(db_file, blob_url)
    return archive

def get_blobstore():
    """
    :returns: a new (or cached) blobstore
    :rtype: memdam.server.blobstore.Blobstore
    """
    blobstore = getattr(flask.g, '_blobstore', None)
    if blobstore is None:
        base_folder = app.config['BLOBSTORE_FOLDER']
        blobstore = flask.g._blobstore = memdam.server.blobstore.Blobstore(base_folder)
    return blobstore

#TODO: evaluate this for security issues. Should probably be careful about user and permissions when writing data.
def make_temp_path():
    """
    :returns: a temporary file name
    :rtype: string
    """
    return tempfile.mktemp()
