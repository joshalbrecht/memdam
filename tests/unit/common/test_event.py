
import json
import uuid

import nose.tools

import memdam.common.timeutils
import memdam.common.event

def test_serialization():
    """Check that converting to and from a json dict gives the same object"""
    event = memdam.common.event.new(
        u"some.data.type",
        cpu__number__percent=0.567,
        a1_2__string__rfc123=u"Didnt+Look+Up+This+Data+Format",
        b__text=u"string for searching",
        c__enum__country=u"USA",
        d__bool=True,
        e__time=memdam.common.timeutils.now(),
        f__id=uuid.uuid4(),
        g__long=184467440737095516L,
        h__file=u"http://somewhere.com/blobs/" + uuid.uuid4().hex + '.txt',
        i__namespace=u"some.thing",
        j__raw=buffer(uuid.uuid4().bytes)
        )
    serialized_json_dict = event.to_json_dict()
    json_string = json.dumps(serialized_json_dict)
    deserialized_json_dict = json.loads(json_string)
    new_event = memdam.common.event.Event.from_json_dict(deserialized_json_dict)
    nose.tools.eq_(new_event, event)

@nose.tools.raises(AssertionError)
def test_immutable():
    """Events should be immutable"""
    event = memdam.common.event.new("some.data.type", temp__long=2**64)
    event.whatever = 15

@nose.tools.raises(AssertionError)
def test_max_long():
    """Should throw an AssertionError if a long attr is >= 2**64"""
    memdam.common.event.new("some.data.type", temp__long=2**64)

if __name__ == '__main__':
    test_serialization()
