
import os
import shutil
import tempfile

import nose.tools

import memdam.recorder.collector.folder
import tests.integration.recorder.collector

class TestFolderUpload(tests.integration.recorder.collector.CollectorTestHarness):
    '''
    Create some files in a folder and make sure that they get uploaded
    '''

    DATA = 'some stuff\nand more lines'

    def __init__(self, *args, **kwargs):
        self._temp_folder = unicode(tempfile.mkdtemp())
        config = dict(namespace=u'com.memdam.folder.testtype', folder=self._temp_folder)
        tests.integration.recorder.collector.CollectorTestHarness.__init__(
            self,
            memdam.recorder.collector.folder.Folder,
            config,
            *args,
            **kwargs
        )

    def setUp(self):
        tests.integration.recorder.collector.CollectorTestHarness.setUp(self)
        for file_name in ('file1', 'file2'):
            path = os.path.join(self._temp_folder, file_name)
            with open(path, 'wb') as out_file:
                out_file.write(self.DATA)
            #make the file super old, then it will definitely get uploaded
            os.utime(path, (0, 0))

    def validate(self, result):
        nose.tools.eq_(len(result), 2)
        sorted_results = sorted(result, key=lambda x: x.name__string)
        nose.tools.eq_(sorted_results[0].name__string, 'file1')
        for i in range(0, len(result)):
            nose.tools.eq_(result[i].size__long, len(self.DATA))

    def tearDown(self):
        shutil.rmtree(self._temp_folder)

if __name__ == '__main__':
    test = TestFolderUpload()
    test.setUp()
    test.runTest()
    test.tearDown()
