
import memdam
import memdam.common.timeutils
import memdam.common.event
import memdam.server.archive.sqlite

def test_save():
    """Test that events can be saved into sqlite"""

    #TODO: remove once I'm satisfied that things are working correctly:
    memdam.log = memdam.create_logger([memdam.STDOUT_HANDLER], memdam.TRACE, name='testlogger')

    #folder = "/tmp"
    folder = ":memory:"
    archive = memdam.server.archive.sqlite.SqliteArchive(folder)
    events = [
        memdam.common.event.Event(memdam.common.timeutils.now(), "somedatatype", some__text="asdfsd", x__text="d"),
        memdam.common.event.Event(memdam.common.timeutils.now(), "somedatatype", some__text="tryr", x__text="g98f"),
    ]
    archive.save(events)

if __name__ == '__main__':
    test_save()
