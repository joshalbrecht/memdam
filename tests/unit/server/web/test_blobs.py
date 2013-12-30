
import uuid
import json

import nose.tools

import memdam.common.utils
import memdam.common.event
import memdam.server.web.utils

import tests.unit.server.web

blob_id = uuid.uuid4()
extension = 'txt'
test_data = 'sdifh3298haskdjghifdughkjfhgs   fsdfih8bsdjfgfd\n'

class CreateTest(tests.unit.server.web.FlaskResourceTestCase):
    def runTest(self):
        """PUTting a blob succeeds"""
        self.headers['Content-Type'] = 'multipart/form-data'
        some_file = memdam.common.utils.make_temp_path()
        with open(some_file, 'wb') as outfile:
            outfile.write(test_data)
        #TODO: figure out how to upload a file to flask
        with self.app.test_request_context('/api/v1/blobs/' + blob_id.hex + "." + extension, method='PUT', files=some_file, headers=self.headers):
            nose.tools.eq_(memdam.server.web.events.events(blob_id.hex), ('', 204))
            result_file = memdam.common.utils.make_temp_path()
            memdam.server.web.utils.get_blobstore().get_data_to_file(blob_id, extension, result_file)
            with open(result_file, 'rb') as infile:
                nose.tools.eq_(infile.read(), test_data)

#class HijackingFilenameTest(tests.unit.server.web.FlaskResourceTestCase):
#    @nose.tools.raises(memdam.server.web.errors.BadRequest)
#    def runTest(self):
#        """PUTting an Event fails without correct Content Type"""
#        new_headers = dict(Authorization=self.headers['Authorization'])
#        with self.app.test_request_context('/api/v1/events/' + event.id__id.hex, method='PUT', data=event_json, headers=new_headers):
#            memdam.server.web.events.events(event.id__id.hex)
#
#class FetchTest(tests.unit.server.web.FlaskResourceTestCase):
#    def runTest(self):
#        """GETting an Event succeeds"""
#        with self.app.test_request_context('/api/v1/events/' + event.id__id.hex, method='GET', data=event_json, headers=self.headers):
#            memdam.server.web.utils.get_archive().save([event])
#            result = memdam.server.web.events.events(event.id__id.hex)
#            # pylint: disable=E1103
#            assert result.status_code == 200
#            assert memdam.common.event.Event.from_json_dict(json.loads(result.data)) == event

if __name__ == '__main__':
    #test = CreateTest()
    test = CreateTest()
    test.setUp()
    test.runTest()
