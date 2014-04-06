
import uuid
import datetime
import re
import os
import sqlite3
import time
import itertools

import pytz
import lockfile

import memdam
import memdam.common.field
import memdam.common.event
import memdam.eventstore.api

@memdam.vtrace()
def execute_sql(cur, sql, args=()):
    '''Just for debugging'''
    return cur.execute(sql, args)

@memdam.vtrace()
def execute_many(cur, sql, values=()):
    '''Just for debugging'''
    cur.executemany(sql, values)

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

    EXTENSION = '.sql'
    LOCK_EXTENSION = '.lock'
    CREATE_TABLE_EXTENSION = '.creating_sql'

    def __init__(self, folder):
        self.folder = folder
        self.memory_connection = None

    def save(self, events):
        memdam.log().debug("Saving events")
        sorted_events = sorted(events, key=lambda x: x.namespace)
        for namespace, grouped_events in itertools.groupby(sorted_events, lambda x: x.namespace):
            table_name = namespace_to_table_name(namespace)
            self._save_events(list(grouped_events), table_name)

    def get(self, event_id):
        for table_name in self._all_table_names():
            conn = self._connect(table_name, read_only=True)
            namespace = table_name_to_namespace(table_name)
            cur = conn.cursor()
            sql = "SELECT * FROM %s WHERE id__id = ?;" % (table_name)
            execute_sql(cur, sql, (buffer(event_id.bytes),))
            names = [x[0] for x in cur.description]
            for row in cur.fetchall():
                return _create_event_from_row(row, names, namespace, conn)
        raise Exception("event with id %s not found" % (event_id))

    def find(self, query):
        events = []
        for table_name in self._all_table_names():
            if _matches_namespace_filters(table_name, query):
                events += self._find_matching_events_in_table(table_name, query)
        return events

    def delete(self, event_id):
        for table_name in self._all_table_names():
            conn = self._connect(table_name, read_only=False)
            cur = conn.cursor()
            cur.execute("BEGIN EXCLUSIVE")
            sql = "SELECT _id FROM %s WHERE id__id = ?;" % (table_name)
            execute_sql(cur, sql, (buffer(event_id.bytes),))
            for row in cur.fetchall():
                rowid = row[0]
                names = [x[0] for x in cur.description]
                for i in range(0, len(names)):
                    name = names[i]
                    if name == '_id':
                        continue
                    if memdam.common.event.Event.field_type(name) == memdam.common.field.FieldType.TEXT:
                        execute_sql(cur, "DELETE FROM %s__%s__docs WHERE docid = ?;" % (table_name, name), (rowid))
                execute_sql(cur, "DELETE FROM %s WHERE _id = %s" % (table_name, rowid), ())
            conn.commit()

    def _find_matching_events_in_table(self, table_name, query):
        conn = self._connect(table_name, read_only=True)
        namespace = table_name_to_namespace(table_name)
        cur = conn.cursor()
        args = ()
        sql = "SELECT * FROM %s" % (table_name)
        field_filters, _ = _separate_filters(query.filters)
        if field_filters:
            filter_string, new_args = _get_field_filter_string(field_filters)
            args = args + new_args
            sql += " WHERE " + filter_string
        if query.order:
            order_string = self._get_order_string(query.order)
            sql += " ORDER BY " + order_string
        if query.limit:
            sql += " LIMIT " + str(long(query.limit))
        sql += ';'
        execute_sql(cur, sql, args)
        events = []
        names = list(map(lambda x: x[0], cur.description))
        for row in cur.fetchall():
            events.append(_create_event_from_row(row, names, namespace, conn))
        return events

    def _get_order_string(self, order):
        sql_order_elems = []
        for elem in order:
            order_type = 'ASC'
            if elem[1] == False:
                order_type = 'DESC'
            safe_column_name = elem[0].lower()
            assert SqliteColumn.SQL_NAME_REGEX.match(safe_column_name), "Invalid name for column: %s" % (safe_column_name)
            assert memdam.common.event.Event.field_type(safe_column_name) != memdam.common.field.FieldType.TEXT, "text keys are currently unsupported for ordering. Doesn't make a lot of sense."
            sql_order_elems.append("%s %s" % (safe_column_name, order_type))
        return ", ".join(sql_order_elems)

    def _all_table_names(self):
        """
        :returns: the names of all tables
        :rtype: list(unicode)
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
        else:
            tables = [r[:-1*len(Eventstore.EXTENSION)] for r in list(os.listdir(self.folder)) if r.endswith(Eventstore.EXTENSION)]
        return [unicode(r) for r in tables]

    def _get_or_create_memory_connection(self):
        assert self.folder == ":memory:"
        #TODO: when all tests are passing again, do we need memory_connection at all? I don't think so...
        if self.memory_connection == None:
            self.memory_connection = sqlite3.connect(self.folder, isolation_level="EXCLUSIVE")
        return self.memory_connection

    def _connect(self, table_name, read_only=True):
        """
        Connect to the database with this namespace in it.
        """
        if self.folder == ":memory:":
            return self._get_or_create_memory_connection()
        db_file = os.path.join(self.folder, table_name + Eventstore.EXTENSION)
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
        memdam.log().debug("Saving %s events to %s" % (len(events), table_name))
        if len(events) <= 0:
            return
        assert SqliteColumn.SQL_NAME_REGEX.match(table_name), "Invalid name for table: %s" % (table_name)

        key_names = set()
        for event in events:
            for key in event.keys:
                key_names.add(key)
        #certain key names are ignored because they are stored implicity in the location of
        #this database (user, namespace)
        for reserved_name in ("type__namespace", "user__id"):
            if reserved_name in key_names:
                key_names.remove(reserved_name)

        should_update_columns = True
        if self.folder != ":memory:":
            #does table not exist?
            db_file = os.path.join(self.folder, table_name + Eventstore.EXTENSION)
            if not os.path.exists(db_file):
                #try to acquire lock
                lock_file = os.path.join(self.folder, table_name + Eventstore.LOCK_EXTENSION)
                lock = lockfile.LockFile(lock_file)
                with lock:
                    #two possible scenarios:
                    #1. we got the lock AFTER someone else, who already made the table:
                    if os.path.exists(db_file):
                        #TODO: move this somewhere more sensible
                        try:
                            os.remove(lock)
                        except:
                            pass
                    #2. we got the lock BEFORE anyone else, so we're responsible for making the table:
                    else:
                        should_update_columns = False
                        #make the table and create the columns
                        temp_db_file = os.path.join(self.folder, table_name + Eventstore.CREATE_TABLE_EXTENSION)
                        self._create_database(table_name, key_names, temp_db_file)
                        #move the file back to it's regular location
                        os.rename(temp_db_file, db_file)
                        #TODO: move this somewhere more sensible
                        try:
                            os.remove(lock)
                        except:
                            pass

        conn = self._connect(table_name, read_only=False)
        if should_update_columns:
            def update_columns():
                cur = conn.cursor()
                existing_columns = self._query_existing_columns(cur, table_name)
                required_columns = self._generate_columns(cur, key_names, table_name)
                self._update_columns(cur, existing_columns, required_columns)
            #TODO: use the locking approach for updating as well as creating?
            execute_with_retries(update_columns, 5)

        cur = conn.cursor()
        cur.execute("BEGIN EXCLUSIVE")
        self._insert_events(cur, events, key_names, table_name)
        conn.commit()

    def _create_database(self, table_name, key_names, db_file):
        assert self.folder != ":memory:", 'because we don\'t have to do this with memory'
        conn = sqlite3.connect(db_file, isolation_level="EXCLUSIVE")
        cur = conn.cursor()
        #TODO: this should NOT have the side-effect of creating the table, that is just weird
        existing_columns = self._query_existing_columns(cur, table_name)
        required_columns = self._generate_columns(cur, key_names, table_name)
        self._update_columns(cur, existing_columns, required_columns)

    def _query_existing_columns(self, cur, table_name):
        """
        :param cur: the current writable database cursor
        :type  cur: sqlite3.Cursor
        :returns: a list of SqliteColumn's
        """
        columns = {}
        execute_sql(cur, "PRAGMA table_info(%s);" % (table_name,))
        allrows = cur.fetchall()
        if len(allrows) == 0:
            self._create_table(cur, table_name)
            execute_sql(cur, "PRAGMA table_info(%s);" % (table_name,))
            allrows = cur.fetchall()
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
        execute_sql(cur, "PRAGMA encoding = 'UTF-8';")
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
        #figure out what the next id to insert should be
        cur.execute("SELECT _id FROM %s ORDER BY _id DESC LIMIT 1" % (table_name))
        next_row_id = 1
        results = cur.fetchall()
        if len(results) > 0:
            next_row_id = results[0][0] + 1

        #need to insert text documents into separate docs tables
        for key in key_names:
            if memdam.common.event.Event.field_type(key) == memdam.common.field.FieldType.TEXT:
                sql = "INSERT INTO %s__%s__docs (docid,data) VALUES (?,?);" % (table_name, key)
                values = [(next_row_id + i, getattr(events[i], key, None)) for i in range(0, len(events))]
                execute_many(cur, sql, values)

        #finally, insert the actual events into the main table
        column_names = list(key_names)
        column_name_string = ", ".join(column_names)
        value_tuple_string = "(" + ", ".join(['?'] * (len(column_names)+1)) + ")"
        sql = "INSERT INTO %s (_id, %s) VALUES %s;" % (table_name, column_name_string, value_tuple_string)
        values = [make_value_tuple(events[i], key_names, next_row_id + i) for i in range(0, len(events))]
        execute_many(cur, sql, values)

#TODO: this whole notion of filters needs to be better thought out
@memdam.vtrace()
def _separate_filters(filters):
    field_filters = []
    namespaces = []
    for f in filters:
        if f.rhs == 'namespace__namespace':
            assert f.operator == '='
            namespaces.append(f.lhs)
        elif f.lhs == 'namespace__namespace':
            assert f.operator == '='
            namespaces.append(f.rhs)
        else:
            field_filters.append(f)
    return field_filters, namespaces

@memdam.vtrace()
def _matches_namespace_filters(table_name, query):
    _, namespaces = _separate_filters(query.filters)
    if len(namespaces) <= 0:
        return True
    return table_name_to_namespace(table_name) in namespaces

@memdam.vtrace()
def _get_field_filter_string(field_filters):
    #TODO (security): lol so bad.
    filter_string = ' AND '.join(('%s %s %s' % (f.lhs, f.operator, f.rhs) for f in field_filters))
    return filter_string, ()

@memdam.vtrace()
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
            elif memdam.common.event.Event.field_type(key) == memdam.common.field.FieldType.TEXT:
                value = event_id
            #convert UUIDs to byte representation
            elif memdam.common.event.Event.field_type(key) == memdam.common.field.FieldType.ID:
                value = buffer(value.bytes)
            elif memdam.common.event.Event.field_type(key) == memdam.common.field.FieldType.FILE:
                value = value.name
        values.append(value)
    return values

@memdam.vtrace()
def convert_time_to_long(value):
    """turns a datetime.datetime into a long"""
    return long(round(1000000.0 * (value - EPOCH_BEGIN).total_seconds()))

@memdam.vtrace()
def convert_long_to_time(value):
    """turns a long into a datetime.datetime"""
    return EPOCH_BEGIN + datetime.timedelta(microseconds=value)

@memdam.vtrace()
def table_name_to_namespace(table_name):
    return table_name.replace(u'_', u'.')

@memdam.vtrace()
def namespace_to_table_name(namespace):
    return namespace.replace(u'.', u'_')

@memdam.vtrace()
def _create_event_from_row(row, names, namespace, conn):
    """returns a memdam.common.event.Event, generated from the row"""
    data = {}
    table_name = namespace_to_table_name(namespace)
    for i in range(0, len(names)):
        name = names[i]
        if name == '_id':
            continue
        value = row[i]
        if value != None:
            field_type = memdam.common.event.Event.field_type(name)
            if field_type == memdam.common.field.FieldType.TIME:
                value = convert_long_to_time(value)
            elif field_type == memdam.common.field.FieldType.TEXT:
                cur = conn.cursor()
                execute_sql(cur, "SELECT data FROM %s__%s__docs WHERE docid = '%s';" % (table_name, name, value))
                value = cur.fetchall()[0][0]
            elif field_type == memdam.common.field.FieldType.ID:
                value = uuid.UUID(bytes=value)
            elif field_type == memdam.common.field.FieldType.BOOL:
                value = value == 1
            elif field_type == memdam.common.field.FieldType.FILE:
                parsed_data = value.split('.')
                value = memdam.common.blob.BlobReference(uuid.UUID(parsed_data[0]), parsed_data[1])
            data[name] = value
    data['type__namespace'] = namespace
    return memdam.common.event.Event(**data)

EPOCH_BEGIN = datetime.datetime(1970, 1, 1, tzinfo=pytz.UTC)

class SqliteColumn(memdam.Base):
    """
    Represents a column in sqlite.
    Note that the name here is the raw key name (eg, without the data type or index)

    :attr name: the name of the column. No type, no index, none of that nonsense.
    :type name: string
    :attr data_type: the type of data
    :type data_type: memdam.common.field.FieldType
    :attr table_name: the name of the table. The namespace for the events
    :type table_name: string
    """

    SQL_NAME_REGEX = re.compile(r"[a-z][a-z0-9_]*")

    data_type_to_sql_type = {
        memdam.common.field.FieldType.NUMBER: 'FLOAT',
        memdam.common.field.FieldType.STRING: 'TEXT',
        #this might seems strange, but it's because we store an index to a document in another table
        memdam.common.field.FieldType.TEXT: 'INTEGER',
        memdam.common.field.FieldType.ENUM: 'TEXT',
        memdam.common.field.FieldType.RAW: 'BLOB',
        memdam.common.field.FieldType.BOOL: 'BOOL',
        memdam.common.field.FieldType.TIME: 'INTEGER',
        memdam.common.field.FieldType.ID: 'TEXT',
        memdam.common.field.FieldType.LONG: 'INTEGER',
        memdam.common.field.FieldType.FILE: 'TEXT',
        memdam.common.field.FieldType.NAMESPACE: 'TEXT',
    }

    def __init__(self, column_name, table_name):
        self.column_name = column_name
        name = memdam.common.event.Event.raw_name(column_name)
        assert SqliteColumn.SQL_NAME_REGEX.match(name), "Invalid name for column: %s" % (name)
        self.name = name
        self.data_type = memdam.common.event.Event.field_type(column_name)
        assert SqliteColumn.SQL_NAME_REGEX.match(name), "Invalid name for table: %s" % (table_name)
        self.table_name = table_name

    @property
    def is_text(self):
        """
        :returns: True iff this is a text "column", which must be handled specially
        """
        return self.data_type == memdam.common.field.FieldType.TEXT

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
        data_type_name = memdam.common.field.FieldType.names[self.data_type]
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
        if self.data_type == memdam.common.field.FieldType.RAW:
            return None
        return 'ASC'

    @staticmethod
    def from_row(row, table_name):
        """
        Alternative constructor from a sqlite row.
        """
        column_name = row[1]
        return SqliteColumn(column_name, table_name)

@memdam.vtrace()
def execute_with_retries(command, num_retries=3, retry_wait_time=0.1, retry_growth_rate=2.0):
    """
    Try to accomplish the command a few times before giving up.
    """
    retry = 0
    last_exception = None
    while retry < num_retries:
        try:
            return command()
        except Exception, e:
            last_exception = e
            time.sleep(retry_wait_time)
            retry_wait_time *= retry_growth_rate
        else:
            break
        retry += 1
    raise last_exception
