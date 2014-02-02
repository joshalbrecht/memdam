
import base64
import json

import flask

import memdam.common.event
import memdam.common.timeutils
import memdam.server.admin
from memdam.server.web.urls import app

NAMESPACE = u'whatever'

class FakeFlaskGlobal(object): pass

#TODO: change this to actually running the web server, insert and query
def test_put_event():
    '''
    Check that events can be saved to the server
    '''
    app.config['DATABASE_FOLDER'] = ':memory:'
    app.config['TESTING'] = True
    username = u'hello'
    password = u'world'
    client = app.test_client()
    #TODO: ew.
    flask.g = FakeFlaskGlobal()
    memdam.server.admin.create_archive(username, password)
    event = memdam.common.event.new(NAMESPACE, cpu__number__percent=0.567)
    event_json = json.dumps(event.to_json_dict())
    result = client.put(u'/api/v1/events/' + event.id__id.hex, data=event_json, headers={
        u'Content-Type': u'application/json',
        u'Authorization': u'Basic ' + base64.b64encode(username + u':' + password)
        })
    assert result.status_code == 204

if __name__ == '__main__':
    test_put_event()
