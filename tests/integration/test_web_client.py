
import time
import multiprocessing

import memdam.common.utils
import memdam.common.timeutils
import memdam.common.client
import memdam.server.web.urls

def test_save_and_get_event_with_file():
    test_data = 'fw98n59askyuesfh.jzlsrkyg'
    server = start_server()
    username = memdam.server.web.urls.app.config['USERNAME']
    password = memdam.server.web.urls.app.config['PASSWORD']
    client = memdam.common.client.MemdamClient("http://127.0.0.1:5000/api/v1/", username, password)
    test_file = memdam.common.utils.make_temp_path() + ".txt"
    with open(test_file, 'wb') as outfile:
        outfile.write(test_data)
    event = memdam.common.event.Event(
        memdam.common.timeutils.now(),
        "some.data.type",
        cpu__number__percent=0.567,
        mydata__file="file://" + test_file,
    )
    client.save_event(event)
    saved_event = client.load_event(event.id__id)
    stop_server(server)

def start_server():
    """Starts up a web server and returns the process"""
    process = multiprocessing.Process(target=run_server)
    process.start()
    time.sleep(1.0)
    return process

def stop_server(server):
    server.terminate()

def run_server():
    memdam.server.web.urls.app.run()

if __name__ == '__main__':
    test_save_and_get_event_with_file()
