
import os
import copy
import argparse

import cherrypy
import cherrypy.wsgiserver
from funcy import *

import memdam.server.web.urls

DEFAULTS = {
    'LISTEN_ADDRESS': '127.0.0.1',
    'LISTEN_PORT': 5000
}

def _load_config_from_file(config_file):
    """Loads the configuration file if defined"""
    if config_file != None:
        assert os.path.exists(config_file), "Config file (%s) does not exist!" % (config_file)
        memdam.server.web.urls.app.config.from_pyfile(config_file, silent=False)

def run(**kwargs):
    """Parses configuration and runs the server"""
    #configuration starts with defaults as defined above
    memdam.server.web.app.config.update(copy.deepcopy(DEFAULTS))
    #if the name of a config file was passed in programmatically, load those settings
    _load_config_from_file(kwargs.get('CONFIG_FILE', None))
    #override anything defined via the kwargs
    memdam.server.web.app.config.update(kwargs)
    #if the name of a config file was defined in an environment variable, load those settings
    _load_config_from_file(os.environ.get('YOURAPPLICATION_SETTINGS', None))

    #fix up the logger
    memdam.log = memdam.server.web.urls.app.logger
    memdam.hack_logger(memdam.log)

    if memdam.server.web.app.config['RUN_WSGI_SERVER']:
        address = memdam.server.web.app.config['LISTEN_ADDRESS']
        port = memdam.server.web.app.config['LISTEN_PORT']
        dispatcher = cherrypy.wsgiserver.WSGIPathInfoDispatcher({'/': memdam.server.web.urls.app})
        server = cherrypy.wsgiserver.CherryPyWSGIServer((address, port), dispatcher)
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()
    else:
        memdam.server.web.urls.app.run(debug=True, use_reloader=False)

def run_as_script():
    """Parses commandline arguments, converting them into the appropriate config variables"""
    parser = argparse.ArgumentParser(description='Run the chronographer server.')
    parser.add_argument('--port', dest='LISTEN_PORT', type=int,
                        help='the port on which to listen')
    parser.add_argument('--host', dest='LISTEN_ADDRESS', type=str,
                        help='the ip address on which to listen')
    parser.add_argument('--wsgi', dest='RUN_WSGI_SERVER', type=bool,
                        help='if true, runs wsgi server for production, if false, runs in debug')
    parser.add_argument('--config', dest='CONFIG_FILE', type=str,
                        help='the path to a file with additional configuration')
    args = parser.parse_args()
    defined_args = select(lambda (k, v): v != None, vars(args))
    run(**defined_args)

if __name__ == '__main__':
    run_as_script()
