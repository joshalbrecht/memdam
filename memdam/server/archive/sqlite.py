
import os
import sqlite3
import itertools

from fn.iters import flatten

import memdam.common.event
import memdam.server.archive.archiveinterface

class SqliteArchive(memdam.server.archive.archiveinterface.ArchiveInterface):
    """
    An archive for all events that uses Sqlite as the backing store.
    Stores all tables in their own file for the following reasons:
    - Lower contention (read and write) when working with multiple data types at once
    - Smaller files (easier to back up, encrypt, decrypt, etc)
    - Safety. Reduces chances of corrupting all data.
    """
    TABLE_NAME = "data"

    #TODO: support in-memory tables too for testing
    def __init__(self, folder):
        self.folder = folder

    def save(self, events):
        #collect all events with the same data_type/device pair
        sorted_events = sorted(events, key=lambda x: x.namespace)
        for table_name, grouped_events in itertools.groupby(sorted_events, lambda x: x.namespace):
            self._save_events(list(grouped_events), table_name)

    def _connect(self, namespace, mode='r'):
        """
        Connect to the database with this namespace in it.
        """
        db_file = os.path.join(self.folder, namespace)
        if mode == 'w':
            return sqlite3.connect(db_file, isolation_level="EXCLUSIVE")
        elif mode == 'r':
            conn = sqlite3.connect(db_file, isolation_level="DEFERRED")
            #TODO: set PRAGMA read_uncommitted = TRUE;
            #otherwise can't read while writing
            return conn
        raise Exception('Invalid database access mode (%s), must be "r" or "w"' % (mode))

    def _save_events(self, events, table_name):
        """
        Save all events of the same type to the database at once
        """
        if len(events) <= 0:
            return
        namespace = events[0].namespace
        conn = self._connect(namespace, 'w')
        cur = conn.cursor()
        existing_columns = self._query_existing_columns(cur)
        key_names = set(flatten([event.keys for event in events]))
        required_columns = self._generate_columns(cur, key_names)
        self._update_columns(cur, existing_columns, required_columns)
        self._insert_events(cur, events)
        conn.commit()

    def _query_existing_columns(self, cur):
        """
        :param cur: the current writable database cursor
        :type  cur: sqlite3.Cursor
        :returns: a list of SqliteColumn's
        """
        columns = []
        cur.execute("PRAGMA table_info(%s)" % (self.TABLE_NAME))
        allrows = cur.fetchall()
        if len(allrows) == 0:
            self._create_table(cur)
            #fetch info again so that there is at least the default column there
            cur.execute("PRAGMA table_info(%s)" % (self.TABLE_NAME))
            allrows = cur.fetchall()
        for row in allrows:
            columns.append(SqliteColumn.from_row(row))
        #now set all index info:
        cur.execute("PRAGMA INDEX_LIST(%s);" % (self.TABLE_NAME))
        index_rows = cur.fetchall()
        for row in index_rows:
            #TODO: actually need to rename indices to be prefixed witih table name, since otherwise we cant put everything in one database in memory
            cur.execute("PRAGMA index_info(sqlite_autoindex_user_1);")
            column_in_index_rows = cur.fetchall()
            #TODO: set index info in columns
            #TODO: maybe this should return a map anyway, since that would be convenient and we need it here
        return columns

    def _create_table(self, cur):
        """
        Create a table with the default column (sample_time)
        """
        cur.execute("CREATE TABLE %s(sample_time INTEGER PRIMARY KEY);" % (self.TABLE_NAME))
        cur.execute("CREATE INDEX sample_time_desc ON %s (sample_time DESC);" % (SqliteArchive.TABLE_NAME))

    def _generate_columns(self, cur, key_names):
        """
        Make a bunch of SqliteColumn's based on the key names of all of the events
        :param cur: the current writable database cursor
        :type  cur: sqlite3.Cursor
        :param key_names: the superset of all key field names
        :type  key_names: set(string)
        :returns: a list of SqliteColumn's
        """
        columns = []
        for key in key_names:
            field_type = memdam.common.event.Event.field_type(key)
            index_type = memdam.common.event.Event.index_type_option(key).get_or(None)
            raw_name = memdam.common.event.Event.raw_name(key)
            columns.append(SqliteColumn(raw_name, field_type, index_type))
        return columns

    def _update_columns(self, cur, existing_columns, required_columns):
        """
        Modify the schema of the table to include new columns or indices if necessary
        """
        existing_column_map = {}
        for existing_column in existing_columns:
            existing_column_map[existing_column.name] = existing_column

        for required_column in required_columns:
            if required_column.name in existing_column_map:
                existing_column = existing_column_map[required_column.name]
                assert required_column.sql_type == existing_column.sql_type
                if required_column.index != existing_column.index:
                    required_column.create_index(cur)
            else:
                required_column.create(cur)

    def _insert_events(self, cur, events):
        """
        Insert all events at once.
        Assumes that the schema is correct.
        """
        #TODO: have to convert datetimes into integers (longs are fine) (microseconds since some epoch I guess)
        #http://stackoverflow.com/questions/12589952/convert-microsecond-timestamp-to-datetime-in-python

class SqliteColumn(object):
    """
    Represents a column in sqlite.
    Note that the name here is the raw key name (eg, without the data type or index)
    """

    def __init__(self, name, sql_type, index=None):
        self.name = name
        self.sql_type = sql_type
        self.index = index

    def create(self, cur):
        cur.execute("ALTER TABLE %s ADD COLUMN ? ?;" % (SqliteArchive.TABLE_NAME), (self.column_name, self.sql_type))
        self.create_index(cur)

    def create_index(self, cur):
        if self.index != None:
            index_name = self.column_name + "_" + self.index
            cur.execute("CREATE INDEX ? ON ? (? ?);", (index_name, SqliteArchive.TABLE_NAME, self.column_name, self.index))

    @property
    def column_name(self):
        return self.name + "_" + self.sql_type

    @staticmethod
    def from_row(row):
        return SqliteColumn(name, sql_type, index)
