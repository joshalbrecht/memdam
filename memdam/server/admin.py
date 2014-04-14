
import re
import os

import flask

import memdam.common.event
import memdam.common.query
import memdam.blobstore.localfolder
import memdam.eventstore.sqlite
import memdam.server.web_server
from memdam.server.web import app

def setup():
    memdam.server.web_server._parse_config(memdam.server.web_server.read_commandline_args())

def create_archive(username, password):
    """
    :param username: the name of the user for which we should get the event archive
    :type  username: string
    :param password: the user's actual password
    :type  password: string
    :returns: a new (or cached) archive
    :rtype: memdam.eventstore.api.Eventstore
    """
    archive = _get_archive(username, must_exist=False)
    archive.save([memdam.common.event.new(u'com.memdam.user.authentication',
                                          username__string=username,
                                          password__string=password)])
    return archive

def _get_archive(username, must_exist=True):
    assert re.compile(r'^[A-Za-z0-9_]+$').match(username)
    db_file = app.config['DATABASE_FOLDER']
    if db_file != ':memory:' and db_file != '':
        db_file = os.path.join(db_file, username)
        if not os.path.exists(db_file):
            if must_exist:
                raise Exception('Archive does not exist: ' + str(db_file))
            else:
                os.makedirs(db_file)
    archive = memdam.eventstore.sqlite.Eventstore(db_file)
    if db_file == ':memory:':
        archives = getattr(flask.g, '_archives', {})
        archives[username] = archive
        flask.g._archives = archives
    return archive

def _get_blobstore(username, must_exist=True):
    assert re.compile(r'^[A-Za-z0-9_]+$').match(username)
    blob_file = app.config['BLOBSTORE_FOLDER']
    blob_file = os.path.join(blob_file, username)
    if not os.path.exists(blob_file):
        if must_exist:
            raise Exception('Archive does not exist: ' + str(blob_file))
        else:
            os.makedirs(blob_file)
    archive = memdam.blobstore.localfolder.Blobstore(blob_file)
    return archive

def find_range(username, namespace=None, start=None, end=None):
    '''
    :param username: the user whose data we should search
    :type  username: string
    :param namespace: if specified, only this namespace should be searched
    :type  namespace: string
    :param start: if specified, only events after this time should be returned
    :type  start: datetime.datetime
    :param end: if specified, only events before this time should be returned
    :type  end: datetime.datetime
    :returns: all of the events matching these criteria
    :rtype: list(memdam.common.event.Event)
    '''
    archive = _get_archive(username)
    filters = []
    if namespace is not None:
        filters.append(memdam.common.query.QueryFilter('namespace__namespace', '=', namespace))
    if start is not None:
        filters.append(memdam.common.query.QueryFilter('time__time', '>=', memdam.eventstore.sqlite.convert_time_to_long(start)))
    if end is not None:
        filters.append(memdam.common.query.QueryFilter('time__time', '<', memdam.eventstore.sqlite.convert_time_to_long(end)))
    query = memdam.common.query.Query(filters=tuple(filters))
    return archive.find(query)

def delete_events(username, events):
    archive = _get_archive(username)
    blobstore = _get_blobstore(username)
    for event in events:
        for field_name, blob_ref in event.blob_ids:
            blobstore.delete(blob_ref)
        archive.delete(event.id__id)

#TODO: for some reason, it doesn't work if I do this. Have to call it from the ipython prompt manually...
#if __name__ == '__main__':
#    setup()
