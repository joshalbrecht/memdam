
import flask

import memdam.common.query
import memdam.server.web.utils
import memdam.server.web.auth

blueprint = flask.Blueprint('queries', __name__)

@blueprint.route('/', methods = ['POST'])
@memdam.server.web.auth.requires_auth
def query_events():
    """
    Create (and executes) a Query, which results in a list of matching Events.

    See answer here for justification of URL :-P
    http://stackoverflow.com/questions/5020704/how-to-design-restful-search-filtering
    """
    if not flask.request.json:
        flask.abort(400)
    query = memdam.common.query.Query.from_json_dict(flask.request.json)
    events = memdam.server.web.utils.get_archive().find(query)
    return flask.jsonify(events)
