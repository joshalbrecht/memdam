
import types
import base64
import datetime
import uuid

import dateutil.parser
from fn.monad import Option

import memdam.common.timeutils
import memdam.common.field
import memdam.common.blob
import memdam.common.validation

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

    Where all named groups start with a-z, are all lower case, and may contain any of a-z0-9_ but
    may not contain more than 1 _ in a row

    The `name` group is the actual name of the attribute.
    Two attributes may not have the same name, even if they must have a different type and/or secondary_name.

    The `type` group refers to a fixed set of acceptable data types.
    All attributes must have one defined.
    See `memdam.common.field.FieldType` for the list of acceptable values (will be lowercased here).
    See the json event-schema for further details on each type.

    The `secondary_type` is optional, and will only ever be defined for NUMBER or STRING types.
    In the case of NUMBER types, `secondary_type` refers to the units of the measurement (ex:
    newtons, inches, etc).
    In the case of STRING types, `secondary_type` refers to the encoding standard used to generate
    the string (ex: iso_3679)
    """

    def __init__(self, **kwargs):
        #TODO: validate the types of all keys
        self.id__id = None
        self.time_time = None
        self.keys = set()
        base_names = set()
        for key, value in kwargs.items():
            key = unicode(key)
            assert value != None, "Can not set attributes to None. If you want to, simply leave it off."
            assert memdam.common.validation.EVENT_FIELD_REGEX.match(key), "Field %s contains something besides a-z_" % (key)
            base_name = key.split('__')[0]
            assert base_name not in base_names, "Duplicated key: " + base_name
            base_names.add(base_name)
            field_type = Event.field_type(key)
            Event.validate(value, field_type)
            assert key == key.lower()
            setattr(self, key, value)
            self.keys.add(key)
        assert hasattr(self, 'id__id')
        assert hasattr(self, 'time__time')
        assert hasattr(self, 'type__namespace')
        self._init_finished = True

    def get_field(self, key):
        """
        :param key: a key from self.keys
        :type  key: string
        :returns: whatever value is associated with that key
        """
        return getattr(self, key)

    @property
    def blob_ids(self):
        """
        :returns: a list of (field_name, blob_ref) tuples, one per file field
        """
        return [(key, self.get_field(key)) for key in self.keys if Event.field_type(key) == memdam.common.field.FieldType.FILE]

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
            elif isinstance(value, memdam.common.blob.BlobReference):
                value = value.to_json()
            if isinstance(value, basestring):
                value = unicode(value)
            new_dict[key] = value
        return new_dict

    def __eq__(self, other):
        return self.to_json_dict().__eq__(other.to_json_dict())

    def __hash__(self):
        return hash(tuple(_make_hash_key(self.to_json_dict())))

    def __setattr__(self, name, value):
        assert not getattr(self, '_init_finished', False), "Events are immutable."
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        assert False, "Events are immutable."

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
        :returns: the memdam.common.field.FieldType for a field with the given name
        :rtype: memdam.common.field.FieldType
        :throws: Exception if the name does not conform to the above specification
        """
        data = name.upper().split('__')
        type_name = data[1]
        return getattr(memdam.common.field.FieldType, type_name)

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
            if field_type == memdam.common.field.FieldType.TIME:
                data[key] = dateutil.parser.parse(data[key])
            elif field_type == memdam.common.field.FieldType.ID:
                data[key] = uuid.UUID(data[key])
            elif field_type == memdam.common.field.FieldType.RAW:
                data[key] = buffer(base64.b64decode(data[key]))
            elif field_type == memdam.common.field.FieldType.FILE:
                data[key] = memdam.common.blob.BlobReference.from_json(data[key])
        return Event(**data)

    @staticmethod
    def validate(value, field_type):
        if field_type == memdam.common.field.FieldType.NUMBER:
            assert isinstance(value, types.FloatType)
        elif field_type in (memdam.common.field.FieldType.STRING, memdam.common.field.FieldType.TEXT, memdam.common.field.FieldType.ENUM):
            assert isinstance(value, unicode)
        elif field_type == memdam.common.field.FieldType.RAW:
            assert isinstance(value, types.BufferType)
        elif field_type == memdam.common.field.FieldType.BOOL:
            assert isinstance(value, types.BooleanType)
        elif field_type == memdam.common.field.FieldType.TIME:
            assert isinstance(value, datetime.datetime)
        elif field_type == memdam.common.field.FieldType.ID:
            assert isinstance(value, uuid.UUID)
        elif field_type == memdam.common.field.FieldType.LONG:
            assert value < 18446744073709551616L
        elif field_type == memdam.common.field.FieldType.FILE:
            assert isinstance(value, memdam.common.blob.BlobReference)
        elif field_type == memdam.common.field.FieldType.NAMESPACE:
            assert isinstance(value, unicode)
            assert memdam.common.validation.NAMESPACE_REGEX.match(value)

def _make_hash_key(data):
    """recursively make a bunch of tuples out of a dict for stable hashing"""
    if isinstance(data, types.TupleType):
        return data
    elif hasattr(data, '__iter__'):
        sorted_keys = sorted([x for x in data])
        return ((key, _make_hash_key(data[key])) for key in sorted_keys)
    return data
