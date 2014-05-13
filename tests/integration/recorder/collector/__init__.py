
import os
import unittest
import shutil

import memdam.common.utils
import memdam.recorder.state
import memdam.blobstore.localfolder
import memdam.eventstore.sqlite

class CollectorTestHarness(unittest.TestCase):
    '''
    A simple test setup for collectors that handles all of the boilerplate.
    '''

    def __init__(self, collector_class, config, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.base_folder = memdam.common.utils.make_temp_path()
        blob_folder = os.path.join(self.base_folder, 'blobs')
        event_folder = os.path.join(self.base_folder, 'events')
        for folder in (blob_folder, event_folder):
            os.makedirs(folder)
        eventstore = memdam.eventstore.sqlite.Eventstore(event_folder)
        blobstore = memdam.blobstore.localfolder.Blobstore(blob_folder)
        state_store = memdam.recorder.state.StateStore(os.path.join(self.base_folder, 'state.json'))
        self.collector = collector_class(config=config,
                                         state_store=state_store,
                                         eventstore=eventstore,
                                         blobstore=blobstore)

    def setUp(self):
        self.collector.start()

    # pylint: disable=C0103
    def runTest(self):
        '''Runs the test. Just starts the collectors, asks for some events, and stops it'''
        result = self.collector.collect_and_persist(10000000)
        self.validate(result)

    def validate(self, result):
        '''
        Use this to check that the collector ran correctly.
        '''
        raise NotImplementedError()

    def tearDown(self):
        self.collector.stop()
        shutil.rmtree(self.base_folder)
