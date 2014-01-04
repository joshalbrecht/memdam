
import uuid

import flask

import memdam.common.event
import memdam.server.web.errors
import memdam.server.web.utils
import memdam.server.web.auth

blueprint = flask.Blueprint('events', __name__)

@blueprint.route('/<unsafe_event_id>', methods = ['PUT', 'GET', 'DELETE'])
@memdam.server.web.auth.requires_auth
def events(unsafe_event_id):
    """
    The only way to create new Events on the server.

    For now, we just create the blob resources separately. Maybe someday they can be created inline too.
    """
    event_id = uuid.UUID(unsafe_event_id)
    if flask.request.method == 'GET':
        event = memdam.server.web.utils.get_archive().get(event_id)
        event_json = event.to_json_dict()
        return flask.jsonify(event_json)
    elif flask.request.method == 'DELETE':
        memdam.server.web.utils.get_archive().delete(event_id)
        return '', 204
    else:
        if not flask.request.json:
            raise memdam.server.web.errors.BadRequest("Must send JSON for events.")
        assert 'id__id' not in flask.request.json or flask.request.json['id__id'] == event_id.hex, \
            "id__id field must be undefined or equal to the id in the event"
        flask.request.json['id__id'] = event_id.hex
        #TODO: run more validation on event json
        event = memdam.common.event.Event.from_json_dict(flask.request.json)
        memdam.server.web.utils.get_archive().save([event])
        return '', 204
