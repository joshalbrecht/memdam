#!flask/bin/python
import flask

import memdam.common.event
import memdam.server.archive.sqlite

app = flask.Flask(__name__)

app.config.update(dict(
    DATABASE='/tmp/default.db',
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
#load settings from the file defined by this variable
app.config.from_envvar('MEMDAM_SETTINGS', silent=True)

def get_archive():
    """
    :returns: a new (or cached) archive
    :rtype: memdam.server.archive.archiveinterface.ArchiveInterface
    """
    archive = getattr(flask.g, '_archive', None)
    if archive is None:
        db_file = app.config['DATABASE']
        archive = flask.g._archive = memdam.server.archive.sqlite.SqliteArchive(db_file)
    return archive

@app.route('/api/v1.0/events/<event_id>', methods = ['PUT'])
def put_event(event_id):
    """
    The only way to create new Events on the server.
    """
    if not flask.request.json:
        flask.abort(400)
    assert 'id__id' not in flask.request.json or flask.request.json['id__id'] == event_id, \
        "id__id field must be defined and equal to the id in the event"
    flask.request.json['id__id'] = event_id
    #TODO: run more validation on event json
    event = memdam.common.event.Event.from_json_dict(flask.request.json)
    get_archive().save([event])
    return '', 204

@app.route('/api/v1.0/events/<event_id>', methods = ['GET'])
def get_event(event_id):
    event = get_archive().get(event_id)
    return flask.jsonify(event)

@app.route('/api/v1.0/events', methods = ['GET'])
def get_events():
    events = get_archive().find(query)
    return flask.jsonify(events)

if __name__ == '__main__':
    app.run(debug = True)
