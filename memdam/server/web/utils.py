
import os

import flask

import memdam.blobstore.localfolder
import memdam.eventstore.sqlite
from memdam.server.web import app

def get_archive(username):
    """
    :param username: the name of the user for which we should get the event archive
    :type  username: string
    :returns: a new (or cached) archive
    :rtype: memdam.eventstore.api.Eventstore
    """
    db_file = app.config['DATABASE_FOLDER']
    if db_file == ':memory:':
        return flask.g._archives[username]

    assert db_file != ''
    db_file = os.path.join(db_file, username)
    if not os.path.exists(db_file):
        os.makedirs(db_file)
    archive = memdam.eventstore.sqlite.Eventstore(db_file)
    return archive

def get_blobstore(username):
    """
    :param username: the name of the user for which we should get the blobstore folder.
    :type  username: string
    :returns: a new (or cached) blobstore
    :rtype: memdam.blobstore.api.Blobstore
    """
    base_folder = app.config['BLOBSTORE_FOLDER']
    user_folder = os.path.join(base_folder, username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    blobstore = memdam.blobstore.localfolder.Blobstore(user_folder)
    return blobstore
