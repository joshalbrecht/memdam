
import types
import datetime

import dateutil.parser
from fn.monad import Option

def enum(*sequential, **named):
    """Create an enum in python < 3.4"""
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['names'] = reverse
    return type('Enum', (), enums)

FieldType = enum('INT', 'FLOAT', 'BINARY', 'TEXT', 'TIME', 'BOOL')
IndexType = enum('FTS', 'ASC', 'DESC')

"""

how exactly to represent Events in memory?
    we want them to be simple and serializable and without any behavior
    but they also need to refer to files somehow (storing the entire thing in memory is too inefficient)
    choices:
            store everything related to the event in memory
                    bad because that's huge and broken
            store ONLY the data that is persisted
                    let's do this.
                    binaries are thus just stored in memory as UUIDs
                    to really use an event, you need to have some separate blobstore that allows you to read and write the binaries
                            can actually even use the same one on the client and server side
                            except that on the client side we always delete the data when finished sending, and on the server side they are NEVER deleted
                            note that the extension is NOT stored, so we are free to convert types, or even store redundant forms, etc
                                    will have to decide about this later
            store different things at different times
            give the event behavior that allows it to access the binary data


events are just json objects with a pretty flat structure
events are objects that have:
    required: sample_time: when the event was recorded. This value is valid between (sample_time - data_window_millis_int, sample_time] if data_window_size is defined
        This, being an integer, is the primary key because you cannot have two events at the same time, which is already stored for every row anyway as the rowid, so this is as efficient as possible
    optional: all other columns.
        If any are new when inserting, alter table to add the columns
        full specification of column names:
            all names are match: ([a-z_]*)_(int|float|binary|text|time|bool)(_(fts|asc|desc))*
            the first group is the name of the column
            the second group is the type of the column
                int: 8 byte integer
                float: 8 byte floating point number
                binary: stored as 16 bytes for a UUID. Events should represent this as a file path internally, with the name UUID.ext
                text: text, variable length, per SQLITE definition
                time: integer. will be stored as the number of milliseconds since UTC start. may be negative if the time is in the past
                bool: boolean. will be stored as an integer
            the third group is optional, and defines what indices to create:
                fts: a FTS4 index for text search. the type must be text
                asc: an ascending index.
                desc: a descending index. Should use this more often, since queries will likely be for more recent data than for super old data.
        examples of optional columns (these are pretty standard):
            (none): implies that this is a "counter" data type. Is recorded whenever we notice it happening, and that is it.
            value_text_fts: searchable text. may be further json for additional processing if you really want. can be large (a whole document). stored as ascii so that it can be lower case searched without changing the case of the data? Also often serves as a "string" version of "value"
            value_real: a numerical measurement
            value_int: special case of the above when this is always going to fit in a long
            data_window_millis_int: the period over which "value" was sampled. number of milliseconds.
            value_binary: special absolute file path (in code), UUID only in sql
        examples of less common possibilities:
            Imagine location: want to save two ints for mouse position: x_int and y_int
            or GPS location: lat_int  and long_int
            or semantic location: location_text_fts
            or postal location: street_text, state_text, zip_text, etc
            or a different searchable field: name_text_fts

"""

class Event(object):
    def __init__(self, sample_time, **kwargs):
        #TODO: events should be immutable and hashable
        self.sample_time = sample_time
        self._keys = set()
        for key, value in kwargs.items():
            #validate that the argument names and types conform to the above specification.
            Event.field_type(key)
            assert key == key.lower()
            setattr(self, key, value)
            if not isinstance(getattr(self, key), types.FunctionType):
                self._keys.add(key)
        self._keys.add('sample_time')

    def has_binary(self):
        """
        :returns: True iff any of the keys contain binary data, False otherwise
        :rtype: bool
        """
        for key in self._keys:
            if Event.field_type(key) == FieldType.BINARY:
                return True
        return False

    def to_json_dict(self):
        """
        Turn this into a dictionary that is suitable for serialization to json
        """
        new_dict = {}
        for key in self._keys:
            value = getattr(self, key)
            if isinstance(value, datetime.datetime):
                value = value.isoformat()
            new_dict[key] = value
        return new_dict

    def __eq__(self, other):
        return self.to_json_dict().__eq__(other.to_json_dict())

    @staticmethod
    def field_type(name):
        """
        :param name: The name of the field to parse
        :type  name: string
        :returns: the FieldType for a field with the given name
        :rtype: FieldType
        :throws: Exception if the name does not conform to the above specification
        """
        data = name.upper().split('_')
        if data[-1] in (IndexType.names.values()):
            data.pop()
        type_name = data.pop()
        return getattr(FieldType, type_name)

    @staticmethod
    def index_type_option(name):
        """
        :param name: The name of the field to parse
        :type  name: string
        :returns: an Option of the IndexType for a field with the given name
        :rtype: Option(IndexType)
        """
        data = name.upper().split('_')
        index = None
        if data[-1] in (IndexType.names.values()):
            index = data.pop()
        return Option.from_value(index)

    @staticmethod
    def from_json_dict(data):
        """
        Convert from a dictionary loaded from JSON to an Event
        """
        for key, value in data.iteritems():
            if Event.field_type(key) == FieldType.TIME:
                data[key] = dateutil.parser.parse(value)
        sample_time = data['sample_time']
        del data['sample_time']
        return Event(sample_time, **data)
