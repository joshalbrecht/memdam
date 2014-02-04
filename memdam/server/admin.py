
import re
import os

import flask

import memdam.common.event
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
    assert re.compile(r'^[A-Za-z0-9_]+$').match(username)
    db_file = app.config['DATABASE_FOLDER']
    if db_file != ':memory:' and db_file != '':
        db_file = os.path.join(db_file, username)
        if not os.path.exists(db_file):
            os.makedirs(db_file)
    archive = memdam.eventstore.sqlite.Eventstore(db_file)
    archive.save([memdam.common.event.new(u'com.memdam.user.authentication',
                                          username__string=username,
                                          password__string=password)])
    if db_file == ':memory:':
        archives = getattr(flask.g, '_archives', {})
        archives[username] = archive
        flask.g._archives = archives
    return archive

#TODO: for some reason, it doesn't work if I do this. Have to call it from the ipython prompt manually...
#if __name__ == '__main__':
#    setup()
