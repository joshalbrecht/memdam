
import memdam
import memdam.common.timeutils
import memdam.common.event
import memdam.server.archive.sqlite

NAMESPACE = "somedatatype"

def test_save():
    """Test that events can be saved into sqlite"""

    #TODO: remove once I'm satisfied that things are working correctly:
    memdam.log = memdam.create_logger([memdam.STDOUT_HANDLER], memdam.TRACE, name='testlogger')

    #folder = "/tmp"
    folder = ":memory:"
    archive = memdam.server.archive.sqlite.SqliteArchive(folder)
    sample_time = memdam.common.timeutils.now
    events = [
        memdam.common.event.Event(sample_time(), NAMESPACE, cpu__number__percent=0.567),
        memdam.common.event.Event(sample_time(), NAMESPACE, some__text="tryr", x__text="g98f"),
        memdam.common.event.Event(sample_time(), NAMESPACE, some__text="asdfsd", x__text="d"),
    ]
    archive.save(events)
    returned_events = set(archive.find())
    assert returned_events == set(events)

if __name__ == '__main__':
    test_save()
