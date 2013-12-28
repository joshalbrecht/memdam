
import base64
import json

import memdam.common.event
import memdam.common.timeutils

import tests.unit.server.web

NAMESPACE = "whatever"

#TODO: abstract this test case
#TODO: make more test cases (put, get, validate each)
#TODO: make test cases of other resources

class EventTest(tests.unit.server.web.FlaskResourceTestCase):
    def runTest(self):
        """
        Check that events can be saved to the server
        """
        event = memdam.common.event.Event(memdam.common.timeutils.now(), NAMESPACE, cpu__number__percent=0.567)
        event_json = json.dumps(event.to_json_dict())
        result = self.client.put('/api/v1/events/' + event.id__id.hex, data=event_json, headers=self.headers)
        # pylint: disable=E1103
        assert result.status_code == 204

if __name__ == '__main__':
    test = EventTest()
    test.setUp()
    test.runTest()
