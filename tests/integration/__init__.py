
import time
import os
import shutil
import tempfile
import multiprocessing

import memdam.server.web_server

def create_test_database(test_name):
    database_folder = os.path.join(tempfile.gettempdir(), test_name)
    if os.path.exists(database_folder):
        shutil.rmtree(database_folder)
    os.makedirs(database_folder)
    return database_folder

def start_server(test_name):
    """Starts up a web server and returns the process"""
    database_folder = create_test_database(test_name)
    config_kwargs = dict(DATABASE_FOLDER=database_folder)
    process = multiprocessing.Process(target=memdam.server.web_server.run, kwargs=config_kwargs)
    process.start()
    time.sleep(1.0)
    return process, database_folder

def stop_server(server):
    server.terminate()
