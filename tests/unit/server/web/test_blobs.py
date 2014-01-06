
import uuid
import json
import StringIO

import nose.tools

import memdam.common.utils
import memdam.common.blob
import memdam.common.event
import memdam.server.web.utils

import tests.unit.server.web

blob_ref = memdam.common.blob.BlobReference(uuid.uuid4(), u'txt')
test_data = 'sdifh3298haskdjghifdughkjfhgs   fsdfih8bsdjfgfd\n'

class CreateTest(tests.unit.server.web.FlaskResourceTestCase):
    def runTest(self):
        """PUTting a blob succeeds"""
        self.headers['Content-Type'] = 'multipart/form-data'
        some_file = memdam.common.utils.make_temp_path()
        with open(some_file, 'wb') as outfile:
            outfile.write(test_data)
        with self.app.test_request_context('/api/v1/blobs/' + blob_ref.name, method='PUT', data={'file': (StringIO.StringIO(test_data), 'test.txt')}, headers=self.headers):
            nose.tools.eq_(memdam.server.web.blobs.blobs(blob_ref.id.hex, blob_ref.extension), ('', 204))
            result_file = memdam.common.utils.make_temp_path()
            memdam.server.web.utils.get_blobstore().get_data_to_file(blob_ref, result_file)
            with open(result_file, 'rb') as infile:
                nose.tools.eq_(infile.read(), test_data)

class HijackingFilenameTest(tests.unit.server.web.FlaskResourceTestCase):
    @nose.tools.raises(memdam.server.web.errors.BadRequest)
    def runTest(self):
        """PUTting an Event fails without correct Content Type"""
        new_headers = dict(Authorization=self.headers['Authorization'])
        new_headers['Content-Type'] = 'multipart/form-data'
        bad_blob_id = blob_ref.id.hex + "...\\/."
        with self.app.test_request_context('/api/v1/blobs/' + bad_blob_id + blob_ref.extension, method='PUT', data={'file': (StringIO.StringIO(test_data), 'test.txt')}, headers=new_headers):
            memdam.server.web.blobs.blobs(bad_blob_id, blob_ref.extension)

class FetchTest(tests.unit.server.web.FlaskResourceTestCase):
    def runTest(self):
        """GETting an Event succeeds"""
        some_file = memdam.common.utils.make_temp_path()
        with open(some_file, 'wb') as outfile:
            outfile.write(test_data)
        with self.app.test_request_context('/api/v1/blobs/' + blob_ref.name, method='GET', headers=self.headers):
            memdam.server.web.utils.get_blobstore().set_data_from_file(blob_ref, some_file)
            response = memdam.server.web.blobs.blobs(blob_ref.id.hex, blob_ref.extension)
            # pylint: disable=E1103
            nose.tools.eq_(response.status_code, 200)
            nose.tools.eq_(response.response.file.read(), test_data)

if __name__ == '__main__':
    test = HijackingFilenameTest()
    test.setUp()
    test.runTest()
