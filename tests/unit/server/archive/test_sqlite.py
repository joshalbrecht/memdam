
import memdam.common.time
import memdam.common.event
import memdam.server.archive.sqlite

def test_save():
    """Test that events can be saved into sqlite"""
    folder = "/tmp"
    device = "testdevice"
    archive = memdam.server.archive.sqlite.SqliteArchive(folder)
    events = [
        memdam.common.event.Event(memdam.common.time.now(), device, "somedatatype", some_text="asdfsd", x_text="d"),
        memdam.common.event.Event(memdam.common.time.now(), device, "somedatatype", some_text="tryr", x_text="g98f"),
    ]
    archive.save(events)

if __name__ == '__main__':
    test_save()
