
import functools

import flask

import memdam.common.query
import memdam.server.web.utils

def check_auth(username, password):
    """
    This function is called to check if a username / password combination is valid.

    :param username: the user's name
    :type  username: unicode
    :param password: the user's password
    :type  password: unicode
    """
    archive = memdam.server.web.utils.get_archive(username)
    most_recent_password_event = archive.find(
        memdam.common.query.Query(
            filters=(memdam.common.query.QueryFilter(u'namespace__namespace', u'=', u'com.memdam.user.authentication'),),
            order=((u'time__time', True),),
            limit=1
        )
    )[0]
    return password == most_recent_password_event.password__string

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return flask.Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(func):
    """A decorator that indicates that the user must authenticate to access this route"""
    @functools.wraps(func)
    def decorated(*args, **kwargs):
        """This code runs before the decorated function to actually check the authentication"""
        auth = flask.request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return func(*args, **kwargs)
    return decorated
