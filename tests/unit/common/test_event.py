
import json

# pylint: disable=E0611,W0611
from nose.tools import assert_raises, assert_equals

import memdam.common.time
import memdam.common.event

def test_serialization():
    """Check that converting to and from a json dict gives the same object"""
    event = memdam.common.event.Event(
        memdam.common.time.now(),
        "some.data.type",
        #TODO: check all supported data types here
        some__text="asdfsd",
        x__text="d")
    serialized_json_dict = event.to_json_dict()
    json_string = json.dumps(serialized_json_dict)
    deserialized_json_dict = json.loads(json_string)
    new_event = memdam.common.event.Event.from_json_dict(deserialized_json_dict)
    assert_equals(new_event, event)

if __name__ == '__main__':
    test_serialization()
