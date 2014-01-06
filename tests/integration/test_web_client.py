
import uuid
import time
import multiprocessing

import nose.tools

import memdam.common.utils
import memdam.common.timeutils
import memdam.common.event
import memdam.common.client
import memdam.blobstore.https
import memdam.eventstore.https
import memdam.server.web.urls
import memdam.server.web_server

def test_save_and_get_event_with_file():
    test_data = 'fw98n59askyuesfh.jzlsrkyg'
    extension = 'txt'
    server = start_server()
    test_file = memdam.common.utils.make_temp_path() + "." + extension
    username = memdam.server.web.urls.app.config['USERNAME']
    password = memdam.server.web.urls.app.config['PASSWORD']
    client = memdam.common.client.MemdamClient("http://127.0.0.1:5000/api/v1/", username, password)
    event = memdam.common.event.new(
        u"some.data.type",
        cpu__number__percent=0.567,
        mydata__file=u"file://"+test_file,
    )
    #test saving an event
    remote_eventstore = memdam.eventstore.https.Eventstore(client)
    remote_eventstore.save([event])
    saved_event = remote_eventstore.get(event.id__id)
    nose.tools.eq_(event, saved_event)

    #test saving a blob
    with open(test_file, 'wb') as outfile:
        outfile.write(test_data)
    remote_blobstore = memdam.blobstore.https.Blobstore(client)
    blob_id = uuid.uuid4()
    remote_blobstore.set_data_from_file(blob_id, extension, test_file)
    response_file = test_file = memdam.common.utils.make_temp_path()
    remote_blobstore.get_data_to_file(blob_id, extension, response_file)
    with open(response_file, 'rb') as infile:
        nose.tools.eq_(test_data, infile.read())

    stop_server(server)

def start_server():
    """Starts up a web server and returns the process"""
    process = multiprocessing.Process(target=memdam.server.web_server.run)
    process.start()
    time.sleep(1.0)
    return process

def stop_server(server):
    server.terminate()

def run_server():
    memdam.server.web.urls.app.run()

if __name__ == '__main__':
    test_save_and_get_event_with_file()
