
import datetime
import re
import os
import sqlite3
import itertools

import pytz
from fn.iters import flatten

import memdam
import memdam.common.event
import memdam.server.archive.archiveinterface

#Just for debugging
def execute_sql(cur, sql, args=()):
    memdam.log.trace("Executing: %s    ARGS=%s" % (sql, args))
    return cur.execute(sql, args)

#TODO: validate the various bits of data--should not start or end with _, should not contain __, should only contain numbers and digits
#also have to validate all of the things that we are inserting in a raw way
class SqliteArchive(memdam.server.archive.archiveinterface.ArchiveInterface):
    """
    An archive for all events that uses Sqlite as the backing store.
    Stores all tables in their own file for the following reasons:
    - Lower contention (read and write) when working with multiple data types at once
    - Smaller files (easier to back up, encrypt, decrypt, etc)
    - Safety. Reduces chances of corrupting all data.

    Note: pass in a folder called :memory: to keep everything in memory for testing
    """

    def __init__(self, folder):
        self.folder = folder

    def save(self, events):
        memdam.log.debug("Saving events")
        sorted_events = sorted(events, key=lambda x: x.namespace)
        for table_name, grouped_events in itertools.groupby(sorted_events, lambda x: x.namespace):
            self._save_events(list(grouped_events), table_name)

    def _connect(self, table_name, mode='r'):
        """
        Connect to the database with this namespace in it.
        """
        if self.folder == ":memory:":
            db_file = self.folder
        else:
            db_file = os.path.join(self.folder, table_name)
        memdam.log.trace("Connecting to %s in %s mode" % (db_file, mode))
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
        memdam.log.trace("Saving %s events to %s" % (len(events), table_name))
        if len(events) <= 0:
            return
        assert re.compile(r"[a-z][a-z_]*").match(table_name), "Should only use a-z and '_' in namespaces"
        conn = self._connect(table_name, 'w')
        cur = conn.cursor()
        existing_columns = self._query_existing_columns(cur, table_name)
        key_names = set(flatten([event.keys for event in events]))
        required_columns = self._generate_columns(cur, key_names, table_name)
        self._update_columns(cur, existing_columns, required_columns)
        self._insert_events(cur, events, key_names, table_name)
        conn.commit()

    def _query_existing_columns(self, cur, table_name):
        """
        :param cur: the current writable database cursor
        :type  cur: sqlite3.Cursor
        :returns: a list of SqliteColumn's
        """
        memdam.log.trace("Looking at existing columns in %s" % (table_name,))
        columns = {}
        execute_sql(cur, "PRAGMA table_info(%s);" % (table_name,))
        allrows = cur.fetchall()
        if len(allrows) == 0:
            self._create_table(cur, table_name)
            execute_sql(cur, "PRAGMA table_info(%s);" % (table_name,))
            allrows = cur.fetchall()
        memdam.log.trace("Table %s info rows: %s" % (table_name, allrows,))
        for row in allrows:
            col = SqliteColumn.from_row(row, table_name)
            columns[col.name] = col
        execute_sql(cur, "PRAGMA INDEX_LIST(%s);" % (table_name,))
        index_rows = cur.fetchall()
        memdam.log.trace("Table %s index rows: %s" % (table_name, allrows,))
        for row in index_rows:
            index_name = row[1]
            execute_sql(cur, "PRAGMA index_info(%s)" % (index_name,))
            column_in_index_rows = cur.fetchall()
            column_components = index_name.split("__")
            #remove table name
            column_components.pop(0)
            index_type = column_components.pop()
            name = column_components[0]
            memdam.log.trace("Table %s column %s has an index of type %s" % (table_name, name, index_type,))
            columns[name].index_type = getattr(memdam.common.event.IndexType, index_type.upper())
        return columns

    def _create_table(self, cur, table_name):
        """
        Create a table with the default column (sample_time)
        """
        memdam.log.trace("Creating default column for %s" % (table_name,))
        execute_sql(cur, "CREATE TABLE %s(sample__time INTEGER PRIMARY KEY);" % (table_name,))
        execute_sql(cur, "CREATE INDEX %s__sample__time__desc ON %s (sample__time DESC);" % (table_name, table_name))

    def _generate_columns(self, cur, key_names, table_name):
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
            columns.append(SqliteColumn(raw_name, field_type, table_name, index_type))
        return columns

    def _update_columns(self, cur, existing_column_map, required_columns):
        """
        Modify the schema of the table to include new columns or indices if necessary
        """

        memdam.log.trace("Should have these columns: %s" % (required_columns,))
        memdam.log.trace("Has these columns: %s" % (existing_column_map,))

        for required_column in required_columns:
            if required_column.name in existing_column_map:
                existing_column = existing_column_map[required_column.name]
                assert required_column.sql_type == existing_column.sql_type
                if required_column.index_type != existing_column.index_type:
                    required_column.create_index(cur)
            else:
                required_column.create(cur)

    def _insert_events(self, cur, events, key_names, table_name):
        """
        Insert all events at once.
        Assumes that the schema is correct.
        """
        #TODO: what to actually call sample_time field?
        #TODO: need to call executemany as per here: http://docs.python.org/2/library/sqlite3.html
        key_names = list(key_names)
        column_names = [make_column_name(x) for x in key_names]
        column_name_string = ", ".join(column_names)
        value_tuple_string = "(" + ", ".join(['?'] * len(column_names)) + ")"
        values_string = ", ".join(len(events) * [value_tuple_string] )
        sql = "INSERT INTO %s (%s) VALUES %s;" % (table_name, column_name_string, values_string)
        values = flatten([make_value_tuple(event, key_names) for event in events])
        execute_sql(cur, sql, values)

def make_value_tuple(event, key_names):
    """Turns an event into a sql value tuple"""
    values = []
    for key in key_names:
        value = getattr(event, key)
        if isinstance(value, datetime.datetime):
            value = int(round(100000.0 * (value - EPOCH_BEGIN).total_seconds()))
        values.append(value)
    return values

EPOCH_BEGIN = datetime.datetime(1970, 1, 1, tzinfo=pytz.UTC)

def make_column_name(key_name):
    """Turns an event attribute name into a sql column name"""
    data = key_name.split("_")
    data_type = data.pop()
    return "_".join(data) + "__" + data_type

class SqliteColumn(object):
    """
    Represents a column in sqlite.
    Note that the name here is the raw key name (eg, without the data type or index)

    :attr name: the name of the column. No type, no index, none of that nonsense.
    :type name: string
    :attr data_type: the type of data
    :type data_type: memdam.common.event.FieldType
    :attr table_name: the name of the table. The namespace for the events
    :type table_name: string
    :attr index_type: the type of the index
    :type index_type: memdam.common.event.IndexType
    """

    data_type_to_sql_type = {
        memdam.common.event.FieldType.INT: 'INTEGER',
        memdam.common.event.FieldType.FLOAT: 'FLOAT',
        memdam.common.event.FieldType.BINARY: 'TEXT',
        memdam.common.event.FieldType.TEXT: 'TEXT',
        memdam.common.event.FieldType.TIME: 'INTEGER',
        memdam.common.event.FieldType.BOOL: 'BOOL',
    }
    index_type_to_sql_type = {
        memdam.common.event.IndexType.FTS: 'FTS',
        memdam.common.event.IndexType.ASC: 'ASC',
        memdam.common.event.IndexType.DESC: 'DESC',
    }

    def __init__(self, name, data_type, table_name, index_type=None):
        assert re.compile(r"[a-z][a-z_]*").match(name.lower()), "Should only use a-z and '_' in namespaces"
        self.name = name.lower()
        self.data_type = data_type
        self.table_name = table_name.lower()
        self.index_type = index_type

    def create(self, cur):
        """
        Create the column and index.
        Only call if the column and index don't already exist.
        """
        execute_sql(cur, "ALTER TABLE %s ADD COLUMN %s %s;" % (self.table_name, self.column_name, self.sql_type))
        self.create_index(cur)

    def create_index(self, cur):
        """
        Create the index, if defined.
        Only call if the index doesn't already exist.
        """
        if self.sql_index != None:
            index_name = self.table_name + "__" + self.column_name + "__" + self.sql_index
            execute_sql(cur, "CREATE INDEX %s ON %s (%s %s);" % (index_name, self.table_name, self.column_name, self.sql_index))

    def __repr__(self):
        data_type_name = memdam.common.event.FieldType.names[self.data_type]
        index_type_name = "None"
        if self.index_type != None:
            index_type_name = memdam.common.event.IndexType.names[self.index_type]
        return "SqliteColumn(%s/%s/%s/%s)" % (self.table_name, self.name, data_type_name, index_type_name)

    def __str__(self):
        return self.__repr__()

    @property
    def sql_type(self):
        """
        :returns: the sqlite type corresponding to our data_type
        :rtype: string
        """
        return self.data_type_to_sql_type[self.data_type]

    @property
    def sql_index(self):
        """
        :returns: the sqlite type corresponding to our index_type
        :rtype: string
        """
        if self.index_type == None:
            return None
        return self.index_type_to_sql_type[self.index_type]

    @property
    def column_name(self):
        """
        :returns: a name to use for the column within the database. Just name + __ + type
        :rtype: string
        """
        data_type_name = memdam.common.event.FieldType.names[self.data_type]
        return self.name + "__" + data_type_name.lower()

    @staticmethod
    def from_row(row, table_name):
        """
        Alternative constructor from a sqlite row.
        """
        column_name = row[1]
        (name, data_type) = column_name.split("__")
        return SqliteColumn(name, getattr(memdam.common.event.FieldType, data_type.upper()), table_name, None)
