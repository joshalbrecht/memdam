
import base64
import json

import memdam.common.event
import memdam.common.timeutils
import memdam.server.web.utils
import memdam.server.web.events

import tests.unit.server.web

NAMESPACE = "whatever"
event = memdam.common.event.Event(memdam.common.timeutils.now(), NAMESPACE, cpu__number__percent=0.567)
event_json = json.dumps(event.to_json_dict())

#TODO: make more test cases (put, get, validate each)
#TODO: make test cases of other resources

class CreateEventTest(tests.unit.server.web.FlaskResourceTestCase):
    def runTest(self):
        """Check that events can be saved to the web server"""
        with self.app.test_request_context('/api/v1/events/' + event.id__id.hex, method='PUT', data=event_json, headers=self.headers) as context:
            assert memdam.server.web.events.events(event.id__id.hex) == ('', 204)
            assert context.g._archive.get(event.id__id) == event

class FetchEventTest(tests.unit.server.web.FlaskResourceTestCase):
    def runTest(self):
        """Check that events can be retrieved from the web server"""
        with self.app.test_request_context('/api/v1/events/' + event.id__id.hex, method='GET', data=event_json, headers=self.headers) as context:
            memdam.server.web.utils.get_archive().save([event])
            result = memdam.server.web.events.events(event.id__id.hex)
            # pylint: disable=E1103
            assert result.status_code == 200
            assert memdam.common.event.Event.from_json_dict(json.loads(result.data)) == event

if __name__ == '__main__':
    #test = CreateEventTest()
    test = FetchEventTest()
    test.setUp()
    test.runTest()
