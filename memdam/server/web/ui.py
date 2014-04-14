
import flask

import memdam.common.query
import memdam.server.web.utils
import memdam.server.web.auth

blueprint = flask.Blueprint('ui', __name__)

@blueprint.route('', methods = ['GET'])
@memdam.server.web.auth.requires_auth
def main_interface():
    """
    Return the HTML interface for interacting with the API from your browser
    """
    return flask.render_template('index.html', name=flask.request.authorization.username)
