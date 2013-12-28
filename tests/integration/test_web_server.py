
import base64
import json

import memdam.common.event
import memdam.common.timeutils
from memdam.server.web.urls import app

NAMESPACE = "whatever"

#TODO: change this to actually running the web server, insert and query
def test_put_event():
    """
    Check that events can be saved to the server
    """
    app.config['DATABASE'] = ":memory:"
    app.config['TESTING'] = True
    client = app.test_client()
    event = memdam.common.event.Event(memdam.common.timeutils.now(), NAMESPACE, cpu__number__percent=0.567)
    event_json = json.dumps(event.to_json_dict())
    result = client.put('/api/v1/events/' + event.id__id.hex, data=event_json, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + base64.b64encode(app.config['USERNAME'] + ":" + app.config['PASSWORD'])
        })
    assert result.status_code == 204

if __name__ == '__main__':
    test_put_event()
