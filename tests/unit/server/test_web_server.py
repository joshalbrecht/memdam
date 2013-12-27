
import json

import memdam.common.event
import memdam.common.timeutils
import memdam.server.web

NAMESPACE = "whatever"

def test_put_event():
    """
    Check that events can be saved to the server
    """
    memdam.server.web.app.config['DATABASE'] = ":memory:"
    memdam.server.web.app.config['TESTING'] = True
    app = memdam.server.web.app.test_client()
    event = memdam.common.event.Event(memdam.common.timeutils.now(), NAMESPACE, cpu__number__percent=0.567)
    event_json = json.dumps(event.to_json_dict())
    result = app.put('/api/v1/events/' + event.id__id.hex, data=event_json, headers={'Content-Type': 'application/json'})
    assert result.status_code == 204

if __name__ == '__main__':
    test_put_event()
