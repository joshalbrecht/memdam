
import uuid
import datetime
import re
import os
import sqlite3
import itertools

import pytz

import memdam
import memdam.common.event
import memdam.eventstore.api

#IndexType = memdam.common.enum.enum('FTS', 'ASC', 'DESC')

#Just for debugging
def execute_sql(cur, sql, args=()):
    memdam.log.trace("Executing: %s    ARGS=%s" % (sql, args))
    return cur.execute(sql, args)

#TODO: store UUIDs as two column integers for better space efficiency
#TODO: validate the various bits of data--should not start or end with _, should not contain __, should only contain numbers and digits
#also have to validate all of the things that we are inserting in a raw way
class Eventstore(memdam.eventstore.api.Eventstore):
    """
    An archive for all events that uses Sqlite as the backing store.
    Stores all tables in their own file for the following reasons:
    - Lower contention (read and write) when working with multiple data types at once
    - Smaller files (easier to back up, encrypt, decrypt, etc)
    - Safety. Reduces chances of corrupting all data.

    Note: pass in a folder called :memory: to keep everything in memory for testing

    blob_url_base should be something like 'https://somewhere.com/some/path/' which is the common
    prefix for all blobs

    When inserting new events, automatically creates new columns if necessary.
    All columns are given appropriate indices (usually ASC, except in the case of TEXT, which is
    given an FTS virtual table, and the column in the main table because an INTEGER that refers
    to the document id in the FTS table)

    Columns are created with exactly the same name as the variables.
    Variable names uniquely define the type of the column, as well as the type of any index.

    TEXT attributes will createa column that contains docid integer references in the main table,
    AS WELL AS a second (virtual, fts4) table (name__text__docs)

    Indices are named "name__type__secondary__indextype"
    """

    def __init__(self, folder, blob_url_base):
        self.folder = folder
        self._blob_url_base = blob_url_base
        self.memory_connection = None

    def save(self, events):
        memdam.log.debug("Saving events")
        sorted_events = sorted(events, key=lambda x: x.namespace)
        for namespace, grouped_events in itertools.groupby(sorted_events, lambda x: x.namespace):
            table_name = namespace.replace(".", "_")
            self._save_events(list(grouped_events), table_name)

    def get(self, event_id):
        for table_name in self._all_table_names():
            conn = self._connect(table_name, read_only=True)
            namespace = table_name.replace("_", ".")
            cur = conn.cursor()
            sql = "SELECT * FROM %s;" % (table_name)
            execute_sql(cur, sql)
            names = [x[0] for x in cur.description]
            for row in cur.fetchall():
                return _create_event_from_row(row, names, namespace, conn)
        raise Exception("event with id %s not found" % (event_id))

    def find(self, query=None):
        #TODO: filter down earlier based on namespace in query
        events = []
        for table_name in self._all_table_names():
            events += self._find_matching_events_in_table(table_name, query)
        return events

    def _find_matching_events_in_table(self, table_name, query):
        #TODO: actually respect query :(
        conn = self._connect(table_name, read_only=True)
        namespace = table_name.replace("_", ".")
        cur = conn.cursor()
        args = ()
        sql = "SELECT * FROM %s;" % (table_name)
        execute_sql(cur, sql, args)
        events = []
        names = list(map(lambda x: x[0], cur.description))
        for row in cur.fetchall():
            events.append(_create_event_from_row(row, names, namespace, conn))
        return events

    def _all_table_names(self):
        """
        :returns: the names of all tables
        :rtype: list(string)
        """
        if self.folder == ":memory:":
            #list all tables that are not "__docs"
            conn = self._get_or_create_memory_connection()
            cur = conn.cursor()
            execute_sql(cur, "SELECT * FROM sqlite_master WHERE type='table';")
            tables = []
            for row in cur.fetchall():
                table_name = row[1]
                if not "__docs" in table_name:
                    tables.append(table_name)
            return tables
        else:
            return os.listdir(self.folder)

    def _get_or_create_memory_connection(self):
        assert self.folder == ":memory:"
        if self.memory_connection == None:
            self.memory_connection = sqlite3.connect(self.folder, isolation_level="EXCLUSIVE")
        return self.memory_connection

    def _connect(self, table_name, read_only=True):
        """
        Connect to the database with this namespace in it.
        """
        if self.folder == ":memory:":
            return self._get_or_create_memory_connection()
        db_file = os.path.join(self.folder, table_name)
        memdam.log.trace("Connecting to %s in read only mode? %s" % (db_file, read_only))
        if read_only:
            conn = sqlite3.connect(db_file, isolation_level="DEFERRED")
            #TODO: set PRAGMA read_uncommitted = TRUE;
            #otherwise can't read while writing
            return conn
        else:
            return sqlite3.connect(db_file, isolation_level="EXCLUSIVE")

    def _save_events(self, events, table_name):
        """
        Save all events of the same type to the database at once
        """
        memdam.log.trace("Saving %s events to %s" % (len(events), table_name))
        if len(events) <= 0:
            return
        assert re.compile(r"[a-z][a-z_]*").match(table_name), "Should only use a-z and '_' in namespaces"
        conn = self._connect(table_name, read_only=False)
        cur = conn.cursor()
        existing_columns = self._query_existing_columns(cur, table_name)
        key_names = set()
        for event in events:
            for key in event.keys:
                key_names.add(key)
        #certain key names are ignored because they are stored implicity in the location of
        #this database (user, namespace)
        for reserved_name in ("type__namespace", "user__id"):
            if reserved_name in key_names:
                key_names.remove(reserved_name)
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
            #ignore our unique id row
            if row[1] == '_id':
                continue
            col = SqliteColumn.from_row(row, table_name)
            columns[col.name] = col
        return columns

    def _create_table(self, cur, table_name):
        """
        Create a table with the default column (sample_time)
        """
        memdam.log.trace("Creating default column for %s" % (table_name,))
        execute_sql(cur, "CREATE TABLE %s(_id INTEGER PRIMARY KEY, time__time INTEGER, id__id STRING);" % (table_name,))
        execute_sql(cur, "CREATE INDEX %s__time__time__asc ON %s (time__time ASC);" % (table_name, table_name))
        execute_sql(cur, "CREATE INDEX %s__id__id__asc ON %s (id__id ASC);" % (table_name, table_name))

    def _generate_columns(self, cur, key_names, table_name):
        """
        Make a bunch of SqliteColumn's based on the key names of all of the events
        :param cur: the current writable database cursor
        :type  cur: sqlite3.Cursor
        :param key_names: the superset of all key field names
        :type  key_names: set(string)
        :returns: a list of SqliteColumn's
        """
        return [SqliteColumn(key, table_name) for key in key_names]

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
            else:
                required_column.create(cur)

    def _insert_events(self, cur, events, key_names, table_name):
        """
        Insert all events at once.
        Assumes that the schema is correct.
        """

        #required because of stupid text fields.
        #we need to explicitly set the ids of everything inserted, or iteratively insert and check for lastrowid (which is slow and pathological and will end up doing this effectively anyway I think)
        cur.execute("BEGIN EXCLUSIVE")

        #figure out what the next id to insert should be
        cur.execute("SELECT _id FROM %s ORDER BY _id DESC LIMIT 1" % (table_name))
        next_row_id = 1
        results = cur.fetchall()
        if len(results) > 0:
            next_row_id = results[0][0] + 1

        #need to insert text documents into separate docs tables
        for key in key_names:
            if memdam.common.event.Event.field_type(key) == memdam.common.event.FieldType.TEXT:
                sql = "INSERT INTO %s__%s__docs (docid,data) VALUES (?,?);" % (table_name, key)
                values = [(next_row_id + i, getattr(events[i], key, None)) for i in range(0, len(events))]
                memdam.log.trace("Executing Many: %s    ARGS=%s" % (sql, values))
                cur.executemany(sql, values)

        #finally, insert the actual events into the main table
        column_names = list(key_names)
        column_name_string = ", ".join(column_names)
        value_tuple_string = "(" + ", ".join(['?'] * (len(column_names)+1)) + ")"
        sql = "INSERT INTO %s (_id, %s) VALUES %s;" % (table_name, column_name_string, value_tuple_string)
        values = [make_value_tuple(events[i], key_names, next_row_id + i) for i in range(0, len(events))]
        memdam.log.trace("Executing Many: %s    ARGS=%s" % (sql, values))
        cur.executemany(sql, values)

def make_value_tuple(event, key_names, event_id):
    """Turns an event into a sql value tuple"""
    values = [event_id]
    for key in key_names:
        value = getattr(event, key, None)
        if value != None:
            #convert time to long for more efficient storage (and so it can be used as a primary key)
            if isinstance(value, datetime.datetime):
                value = convert_time_to_long(value)
            #convert text tuple entries into references to the actual text data
            elif memdam.common.event.Event.field_type(key) == memdam.common.event.FieldType.TEXT:
                value = event_id
            #convert UUIDs to byte representation
            elif memdam.common.event.Event.field_type(key) == memdam.common.event.FieldType.ID:
                value = buffer(value.bytes)
        values.append(value)
    return values

def convert_time_to_long(value):
    """turns a datetime.datetime into a long"""
    return long(round(1000000.0 * (value - EPOCH_BEGIN).total_seconds()))

def convert_long_to_time(value):
    """turns a long into a datetime.datetime"""
    return EPOCH_BEGIN + datetime.timedelta(microseconds=value)

def _create_event_from_row(row, names, namespace, conn):
    """returns a memdam.common.event.Event, generated from the row"""
    data = {}
    table_name = namespace.replace(".", "_")
    for i in range(0, len(names)):
        name = names[i]
        if name == '_id':
            continue
        value = row[i]
        if value != None:
            field_type = memdam.common.event.Event.field_type(name)
            if field_type == memdam.common.event.FieldType.TIME:
                value = convert_long_to_time(value)
            elif field_type == memdam.common.event.FieldType.TEXT:
                cur = conn.cursor()
                execute_sql(cur, "SELECT data FROM %s__%s__docs WHERE docid = '%s';" % (table_name, name, value))
                value = cur.fetchall()[0][0]
            elif field_type == memdam.common.event.FieldType.ID:
                value = uuid.UUID(bytes=value)
        data[name] = value
    sample_time = data['time__time']
    del data['time__time']
    return memdam.common.event.Event(sample_time, namespace, **data)

EPOCH_BEGIN = datetime.datetime(1970, 1, 1, tzinfo=pytz.UTC)

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
    """

    data_type_to_sql_type = {
        memdam.common.event.FieldType.NUMBER: 'FLOAT',
        memdam.common.event.FieldType.STRING: 'TEXT',
        #this might seems strange, but it's because we store an index to a document in another table
        memdam.common.event.FieldType.TEXT: 'INTEGER',
        memdam.common.event.FieldType.ENUM: 'TEXT',
        memdam.common.event.FieldType.RAW: 'BLOB',
        memdam.common.event.FieldType.BOOL: 'BOOL',
        memdam.common.event.FieldType.TIME: 'INTEGER',
        memdam.common.event.FieldType.ID: 'TEXT',
        memdam.common.event.FieldType.LONG: 'INTEGER',
        memdam.common.event.FieldType.FILE: 'TEXT',
        memdam.common.event.FieldType.NAMESPACE: 'TEXT',
    }

    def __init__(self, column_name, table_name):
        self.column_name = column_name
        name = memdam.common.event.Event.raw_name(column_name)
        assert re.compile(r"[a-z][a-z_]*").match(name.lower()), "Should only use a-z and '_' in namespaces"
        self.name = name.lower()
        self.data_type = memdam.common.event.Event.field_type(column_name)
        self.table_name = table_name.lower()

    @property
    def is_text(self):
        """
        :returns: True iff this is a text "column", which must be handled specially
        """
        return self.data_type == memdam.common.event.FieldType.TEXT

    def create(self, cur):
        """
        Create the column and index.
        Only call if the column and index don't already exist.
        """
        if self.is_text:
            execute_sql(cur, "CREATE VIRTUAL TABLE %s__%s__docs USING fts4(data,tokenize=porter);" % (self.table_name, self.column_name))
        execute_sql(cur, "ALTER TABLE %s ADD COLUMN %s %s;" % (self.table_name, self.column_name, self.sql_type))
        if self.sql_index != None:
            index_name = self.table_name + "__" + self.column_name + "__" + self.sql_index
            execute_sql(cur, "CREATE INDEX %s ON %s (%s %s);" % (index_name, self.table_name, self.column_name, self.sql_index))

    def __repr__(self):
        data_type_name = memdam.common.event.FieldType.names[self.data_type]
        return "SqliteColumn(%s/%s/%s)" % (self.table_name, self.name, data_type_name)

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
        Note: everything returns ASC because the only alternative is FTS, which is handled specially
        and ends up making an ASC index on the column anyway.
        :returns: the sqlite type corresponding to our index type
        :rtype: string
        """
        if self.data_type == memdam.common.event.FieldType.RAW:
            return None
        return 'ASC'

    @staticmethod
    def from_row(row, table_name):
        """
        Alternative constructor from a sqlite row.
        """
        column_name = row[1]
        return SqliteColumn(column_name, table_name)
