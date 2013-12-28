
import base64
import json

import nose.tools

import memdam.common.event
import memdam.common.timeutils
import memdam.server.web.utils
import memdam.server.web.events

import tests.unit.server.web

event = memdam.common.event.Event(memdam.common.timeutils.now(), "whatever", cpu__number__percent=0.567)
event_json = json.dumps(event.to_json_dict())

#TODO: make client
#TODO: test client
#TODO: make test cases of other resources

class CreateTest(tests.unit.server.web.FlaskResourceTestCase):
    def runTest(self):
        """PUTting an Event succeeds"""
        with self.app.test_request_context('/api/v1/events/' + event.id__id.hex, method='PUT', data=event_json, headers=self.headers):
            assert memdam.server.web.events.events(event.id__id.hex) == ('', 204)
            assert memdam.server.web.utils.get_archive().get(event.id__id) == event

class NoJsonErrorTest(tests.unit.server.web.FlaskResourceTestCase):
    @nose.tools.raises(memdam.server.web.errors.BadRequest)
    def runTest(self):
        """PUTting an Event fails without correct Content Type"""
        new_headers = dict(Authorization=self.headers['Authorization'])
        with self.app.test_request_context('/api/v1/events/' + event.id__id.hex, method='PUT', data=event_json, headers=new_headers):
            memdam.server.web.events.events(event.id__id.hex)

class FetchTest(tests.unit.server.web.FlaskResourceTestCase):
    def runTest(self):
        """GETting an Event succeeds"""
        with self.app.test_request_context('/api/v1/events/' + event.id__id.hex, method='GET', data=event_json, headers=self.headers):
            memdam.server.web.utils.get_archive().save([event])
            result = memdam.server.web.events.events(event.id__id.hex)
            # pylint: disable=E1103
            assert result.status_code == 200
            assert memdam.common.event.Event.from_json_dict(json.loads(result.data)) == event

class NoAuthenticationTest(tests.unit.server.web.FlaskResourceTestCase):
    def runTest(self):
        """GETting an Event fails without authentication"""
        with self.app.test_request_context('/api/v1/events/' + event.id__id.hex, method='GET', data=event_json, headers={}):
            result = memdam.server.web.events.events(event.id__id.hex)
            # pylint: disable=E1103
            assert result.status_code == 401

if __name__ == '__main__':
    #test = CreateTest()
    test = FetchTest()
    test.setUp()
    test.runTest()
