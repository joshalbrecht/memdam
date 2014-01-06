
import uuid
import re

import memdam.common.validation

class BlobReference(object):
    """
    A Python reference to a blob. Just contains the uuid.UUID and extension
    """

    def __init__(self, uid, extension):
        assert isinstance(uid, uuid.UUID)
        assert isinstance(extension, unicode)
        assert re.compile(u"^" + memdam.common.validation.EXTENSION_PATTERN + u"$").match(extension)
        # pylint: disable=C0103
        self.id = uid
        self.extension = extension
        self._init_finished = True

    @property
    def name(self):
        """
        :returns: the bare file name for thie blob, effectively (uuid.extension)
        :rtype: unicode
        """
        return u"%s.%s" % (self.id.hex, self.extension)

    def to_tuple(self):
        """
        :returns: the canonical tuple for this blob id (for hashing and serialization)
        :rtype: (uuid.UUID, unicode)
        """
        return (self.id, self.extension)

    def to_json(self):
        """
        :returns: a json representation of this object
        :rtype: (unicode, unicode)
        """
        return (unicode(self.id.hex), self.extension)

    def __eq__(self, other):
        return self.to_tuple().__eq__(other.to_tuple())

    def __hash__(self):
        return hash(self.to_tuple())

    def __setattr__(self, name, value):
        assert not getattr(self, "_init_finished", False), "BlobReference's are immutable."
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        assert False, "BlobReference's are immutable."

    @staticmethod
    def from_json(data):
        """
        :returns: A BlobReference, created from json data
        :rtype: BlobReference
        """
        return BlobReference(uuid.UUID(data[0]), data[1])
