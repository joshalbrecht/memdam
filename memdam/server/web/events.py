
import flask

import memdam.common.event
import memdam.server.web.utils
import memdam.server.web.auth

blueprint = flask.Blueprint('events', __name__)

#TODO: inline blob handling
@blueprint.route('/<event_id>', methods = ['PUT', 'GET'])
@memdam.server.web.auth.requires_auth
def events(event_id):
    """
    The only way to create new Events on the server.

    For now, we just create the blob resources separately. Maybe someday they can be created inline too.
    """
    if flask.request.method == 'GET':
        event = memdam.server.web.utils.get_archive().get(event_id)
        event_json = event.to_json_dict()
        return flask.jsonify(event_json)
    else:
        if not flask.request.json:
            flask.abort(400)
        assert 'id__id' not in flask.request.json or flask.request.json['id__id'] == event_id, \
            "id__id field must be undefined or equal to the id in the event"
        flask.request.json['id__id'] = event_id
        #TODO: run more validation on event json
        event = memdam.common.event.Event.from_json_dict(flask.request.json)
        memdam.server.web.utils.get_archive().save([event])
        return '', 204
