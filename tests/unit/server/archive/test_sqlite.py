
import shutil
import uuid
import os
import unittest

import nose.tools

import memdam
import memdam.common.utils
import memdam.common.timeutils
import memdam.common.event
import memdam.eventstore.sqlite

NAMESPACE = "somedatatype"

class SqliteBase(unittest.TestCase):
    """
    Defines all unit tests to run on our sqlite archive.

    Note that each test is effectively run twice--once in-memory, and once on-disk--since there are
    slightly different behaviors in each case.
    """

    #TODO: possible to delete this?
    def runTest(self, ):
        pass

    def __init__(self, folder, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.blob_url = "https://127.0.0.1/testcasepath"
        self.archive = memdam.eventstore.sqlite.Eventstore(folder, self.blob_url)
        self.simple_event = memdam.common.event.Event(
            memdam.common.timeutils.now(),
            NAMESPACE,
            cpu__number__percent=0.567)
        self.complex_event = memdam.common.event.Event(
            memdam.common.timeutils.now(),
            NAMESPACE,
            cpu__number__percent=0.567,
            a__string__rfc123="Didnt+Look+Up+This+Data+Format",
            b__text="string for searching",
            c__enum__country="USA",
            d__bool=True,
            e__time=memdam.common.timeutils.now(),
            f__id=uuid.uuid4(),
            g__long=184467440737095516L,
            h__file=self.blob_url + "/" + uuid.uuid4().hex + '.txt',
            i__namespace="some.thing",
            j__raw=buffer(uuid.uuid4().bytes),
        )

    def test_get(self):
        """Getting a single Event by id should succeed"""
        self.archive.save([self.simple_event])
        nose.tools.eq_(self.archive.get(self.simple_event.id__id), self.simple_event)

    @nose.tools.raises(Exception)
    def test_get_fails_with_bad_id(self):
        """Getting a single Event by id should raise an Exception if the id is not defined"""
        self.archive.get(uuid.uuid4())

    def test_save_multiple_times(self):
        """Saving lots of events (and events twice) should succeed"""
        self.archive.save([self.complex_event])
        self.archive.save([self.complex_event])
        self.archive.save([self.simple_event])
        returned_events = set(self.archive.find())
        nose.tools.eq_(returned_events, set([self.complex_event, self.simple_event]))

    def test_save_all_data_types(self):
        """Saving and loading an event should work with all data types"""
        self.archive.save([self.complex_event])
        returned_events = set(self.archive.find())
        nose.tools.eq_(returned_events, set([self.complex_event]))

    def test_save_multiple_events_at_once(self):
        """Saving multiple Events should succeed"""
        sample_time = memdam.common.timeutils.now
        events = [
            memdam.common.event.Event(sample_time(), NAMESPACE, cpu__number__percent=0.567),
            memdam.common.event.Event(sample_time(), NAMESPACE, some__text="tryr", x__text="g98f"),
            memdam.common.event.Event(sample_time(), NAMESPACE, some__text="asdfsd", x__text="d"),
        ]
        self.archive.save(events)
        returned_events = set(self.archive.find())
        nose.tools.eq_(returned_events, set(events))

    #TODO: decide whether attributes with the same name and different types are allowed, and make a test
    #TODO (far future) test queries

class MemoryTest(SqliteBase):
    """Run all sqlite archive tests with the in-memory database"""
    def __init__(self, *args, **kwargs):
        SqliteBase.__init__(self, ":memory:", *args, **kwargs)

class LocalFileTest(SqliteBase):
    """Run all sqlite archive tests with the on-disk database"""
    def __init__(self, *args, **kwargs):
        SqliteBase.__init__(self, None, *args, **kwargs)

    def setUp(self, ):
        self._temp_file = memdam.common.utils.make_temp_path()
        os.mkdir(self._temp_file)
        self.archive = memdam.eventstore.sqlite.Eventstore(self._temp_file, self.blob_url)

    def tearDown(self):
        if os.path.exists(self._temp_file):
            shutil.rmtree(self._temp_file)

if __name__ == '__main__':
    tester = MemoryTest()
    tester.setUp()
    tester.test_save_multiple_times()
    tester.tearDown()
