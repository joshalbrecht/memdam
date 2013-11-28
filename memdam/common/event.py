
import types
import datetime

import dateutil.parser
from fn.monad import Option

import memdam.common.enum

FieldType = memdam.common.enum.enum('NUMBER', 'STRING', 'TEXT', 'ENUM', 'BOOL', 'TIME', 'ID', 'LONG', 'FILE')

class Event(object):
    """
    The class that represents all events.

    All events are immutable and hash properly.

    There are two required parameters:

    :attr time: The time at which this Event happened
    :type time: datetime.datetime
    :attr namespace: A specially formatted string that effectively maps to the expected schema for
    the rest of the Event field. Reverse domain like java packages. Ex: com.memdam.email
    :type namespace: string

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

    SPECIAL_NAME_TYPES = {
        'time': FieldType.TIME,
        'namespace': FieldType.STRING,
        'id': FieldType.ID,
        'source': FieldType.ID,
        'user': FieldType.ID,
    }

    def __init__(self, sample_time, namespace, **kwargs):
        #TODO: events should be immutable and hashable
        #TODO: validate all keys (allowable characters, correct type, no overlap with top level, etc)
        self.namespace = namespace
        self.time = sample_time
        self.keys = set()
        for key, value in kwargs.items():
            #validate that the argument names and types conform to the above specification.
            Event.field_type(key)
            assert key == key.lower()
            setattr(self, key, value)
            if not isinstance(getattr(self, key), types.FunctionType):
                self.keys.add(key)
        self.keys.add('time')
        self.keys.add('namespace')

    def get_field(self, key):
        """
        :param key: a key from self.keys
        :type  key: string
        :returns: whatever value is associated with that key
        """
        return getattr(self, key)

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
            new_dict[key] = value
        return new_dict

    def __eq__(self, other):
        return self.to_json_dict().__eq__(other.to_json_dict())

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
        if name in Event.SPECIAL_NAME_TYPES:
            return Event.SPECIAL_NAME_TYPES[name]
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
        if name in Event.SPECIAL_NAME_TYPES:
            return Option.from_value(None)
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
            if Event.field_type(key) == FieldType.TIME:
                data[key] = dateutil.parser.parse(data[key])
        sample_time = data['time']
        del data['time']
        namespace = data['namespace']
        del data['namespace']
        return Event(sample_time, namespace, **data)
