
import re
import base64
import types
import datetime
import uuid

import dateutil.parser
from fn.monad import Option

import memdam.common.timeutils
import memdam.common.enum

FieldType = memdam.common.enum.enum('NUMBER', 'STRING', 'TEXT', 'ENUM', 'RAW', 'BOOL', 'TIME', 'ID', 'LONG', 'FILE', 'NAMESPACE')

SUPPORTED_URLS = ('file://', 'http://', 'https://')
FILE_REGEX = re.compile(r'^[a-f0-9]{32}\.[a-z0-9]+$')

def new(namespace, **kwargs):
    """Convenience function for the creation of events"""
    kwargs['type__namespace'] = namespace
    kwargs['time__time'] = memdam.common.timeutils.now()
    kwargs['id__id'] = uuid.uuid4()
    return Event(**kwargs)

class Event(object):
    """
    The class that represents all events.

    All events are immutable and hash properly.

    There are two required parameters:

    :attr time__id: The time at which this Event happened
    :type time__id: datetime.datetime
    :attr type__namespace: A specially formatted string that effectively maps to the expected schema for
    the rest of the Event field. Reverse domain like java packages. Ex: com.memdam.email
    :type type__namespace: string

    All other parameters are dynamic, and follow the form:
    ^(?P=name)__(?P=type)(__(?P=secondary_type))?$

    Where all named groups match:
    ^([a-z]+_)*[a-z]+$

    The `name` group is the actual name of the attribute.
    Two attributes may have the same name, but they must have a different type and/or secondary_name.

    The `type` group refers to a fixed set of acceptable data types.
    All attributes must have one defined.
    See `FieldType` above for the list of acceptable values (will be lowercased here).
    See the json event-schema for further details on each type.

    The `secondary_type` is optional, and will only ever be defined for NUMBER or STRING types.
    In the case of NUMBER types, `secondary_type` refers to the units of the measurement (ex:
    newtons, inches, etc).
    In the case of STRING types, `secondary_type` refers to the encoding standard used to generate
    the string (ex: iso_3679)
    """

    def __init__(self, **kwargs):
        #TODO: events should be immutable and hashable
        #TODO: validate all keys (allowable characters, correct type, no overlap with top level, etc)
        self.id__id = None
        self.time_time = None
        self.keys = set()
        for key, value in kwargs.items():
            key = unicode(key)
            if value != None:
                #validate that the argument names and types conform to the above specification.
                field_type = Event.field_type(key)
                if field_type == FieldType.LONG:
                    assert value < 18446744073709551616L
                if field_type == FieldType.FILE:
                    lowered = value.lower()
                    assert len([True for url_type in SUPPORTED_URLS if lowered.startswith(url_type)]) > 0, "All file variables must use one of the following url schemes: " + SUPPORTED_URLS
                    assert '/' in lowered, "must use absolute file urls for file type variables"
                    assert FILE_REGEX.match(lowered.split('/')[-1]), "file names must be of the form hexuuid.extension"
                if isinstance(value, basestring):
                    value = unicode(value)
                assert key == key.lower()
                setattr(self, key, value)
                self.keys.add(key)
        assert hasattr(self, 'id__id')
        assert hasattr(self, 'time__time')
        assert hasattr(self, 'type__namespace')

    def get_field(self, key):
        """
        :param key: a key from self.keys
        :type  key: string
        :returns: whatever value is associated with that key
        """
        return getattr(self, key)

    def get_file_data(self, key):
        """
        :param key: a key from self.keys
        :type  key: string
        :returns: a tuple with detailed data about the file field: (blob_id, extension)
        :rtype: (uuid.UUID, string)
        """
        url = self.get_field(key)
        filename = url.split('/')[-1]
        data = filename.split('.')
        return (data[:-1], data[-1])

    def has_file(self):
        """
        :returns: True iff any of the keys contain binary data, False otherwise
        :rtype: bool
        """
        for key in self.keys:
            if Event.field_type(key) == FieldType.FILE:
                return True
        return False

    def to_json_dict(self):
        """
        Turn this into a dictionary that is suitable for serialization to json
        """
        new_dict = {}
        for key in self.keys:
            value = getattr(self, key)
            if isinstance(value, datetime.datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = value.hex
            elif isinstance(value, buffer):
                value = base64.b64encode(value)
            if isinstance(value, basestring):
                value = unicode(value)
            new_dict[key] = value
        return new_dict

    def __eq__(self, other):
        return self.to_json_dict().__eq__(other.to_json_dict())

    def __hash__(self):
        return hash(tuple(_make_hash_key(self.to_json_dict())))

    @property
    def time(self):
        """
        Just a shortcut for time__time
        :returns: the time that this Event occurred
        :rtype: datetime.datetime
        """
        return self.time__time

    @property
    def namespace(self):
        """
        Just a shortcut for type__namespace
        :returns: the namespace for this event
        :rtype: string
        """
        return self.type__namespace

    @staticmethod
    def raw_name(name):
        """
        :param name: The name of the field to parse
        :type  name: string
        :returns: the name, with any type and index information stripped off
        :rtype: string
        :throws: Exception if the name does not conform to the above specification
        """
        return name.split('__')[0]

    @staticmethod
    def field_type(name):
        """
        :param name: The name of the field to parse
        :type  name: string
        :returns: the FieldType for a field with the given name
        :rtype: FieldType
        :throws: Exception if the name does not conform to the above specification
        """
        data = name.upper().split('__')
        type_name = data[1]
        return getattr(FieldType, type_name)

    @staticmethod
    def secondary_type_option(name):
        """
        :param name: The name of the field to parse
        :type  name: string
        :returns: an Option of the secondary type for a field with the given name (empty if there is
        no secondary type)
        :rtype: Option(secondaryType)
        """
        data = name.upper().split('__')
        if len(data) > 2:
            return Option.from_value(data.pop())
        return Option.from_value(None)

    @staticmethod
    def from_json_dict(data):
        """
        Convert from a dictionary loaded from JSON to an Event
        """
        keys = list(data.keys())
        for key in keys:
            field_type = Event.field_type(key)
            if field_type == FieldType.TIME:
                data[key] = dateutil.parser.parse(data[key])
            elif field_type == FieldType.ID:
                data[key] = uuid.UUID(data[key])
            elif field_type == FieldType.RAW:
                data[key] = buffer(base64.b64decode(data[key]))
        return Event(**data)

def _make_hash_key(data):
    """recursively make a bunch of tuples out of a dict for stable hashing"""
    if hasattr(data, '__iter__'):
        sorted_keys = sorted([x for x in data])
        return ((key, _make_hash_key(data[key])) for key in sorted_keys)
    return data
