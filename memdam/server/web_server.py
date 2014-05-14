
import sys
import os
import argparse
import logging

import cherrypy
import cherrypy.wsgiserver
# pylint: disable=W0401,W0622,W0614
from funcy import *

import memdam.server.admin
import memdam.server.web.urls

def _load_config_from_file(config_file, config_source):
    '''Loads the configuration file if defined'''
    if config_file != None:
        assert os.path.exists(config_file), 'Config file (%s) does not exist!' % (config_file)
        memdam.server.web.urls.app.config.from_pyfile(config_file, silent=False)
        _update_config_source(config_source, memdam.server.web.app.config, 'FILE=' + config_file)

def _update_config_source(source, config, name):
    '''
    :param source: a dictionary tracking both the current config value, and where it came from.
    :type  source: dict(string -> (string(value), string(source)))
    :param config: the web app configuration
    :type  config: ???
    :param name: the name of the source that most recently updated config
    :type  name: string
    '''
    for key in config:
        if key in source:
            if source[key][0] != config[key]:
                source[key] = (config[key], name)
        else:
            source[key] = (config[key], name)

def _format_config_value(value, key):
    '''
    Hides secret configuration variables when printing config.
    '''
    if key in ('SECRET_KEY',):
        return '******'
    return value

def _format_config_source(source, ordered_sources):
    '''
    :returns: string (describing the source and value of each configuration variable)
    '''
    grouped_keys = group_by(lambda key: source[key][1], source.keys())
    formatted_group_configs = []
    for source_name in ordered_sources:
        if source_name in grouped_keys:
            keys_for_source = grouped_keys[source_name]
            formatted_values = '\n'.join(['    %s=%s' % (key, _format_config_value(source[key][0], key)) \
                                          for key in sorted(keys_for_source)])
            formatted_group_configs.append('%s:\n%s' % (source_name, formatted_values))
    return 'Current Configuration:\n' + '\n'.join(formatted_group_configs)

def _parse_config(kwargs):
    '''
    Parses the configuration from a variety of sources into memdam.server.web.app.config

    Also applies the settings to the logger because that should happen as early as possible in the
    process. Probably should not make calls to memdam.log() before this.

    :param kwargs: a dictionary of the config arguments that should be applied for this run.
    :type  kwargs: dict
    '''
    #track which configuration came from where for our own sanity:
    config_source = {}
    _update_config_source(config_source, memdam.server.web.app.config, 'DEFAULT')

    #if the name of a config file was passed in programmatically, load those settings
    _load_config_from_file(kwargs.get('CONFIG_FILE', None), config_source)
    #override anything defined via the kwargs
    memdam.server.web.app.config.update(kwargs)
    _update_config_source(config_source, memdam.server.web.app.config, 'KWARGS')
    #if the name of a config file was defined in an environment variable, load those settings
    _load_config_from_file(os.environ.get('YOURAPPLICATION_SETTINGS', None), config_source)

    ordered_sources = remove(lambda x: x == None, ('DEFAULT', kwargs.get('CONFIG_FILE', None), 'KWARGS', os.environ.get('YOURAPPLICATION_SETTINGS', None)))
    config_message = _format_config_source(config_source, ordered_sources)
    print(config_message)

    #fix up the logger
    memdam._logger = memdam.server.web.urls.app.logger
    memdam.hack_logger(memdam._logger)
    memdam._logger.setLevel(getattr(logging, memdam.server.web.app.config['LOG_LEVEL']))
    memdam.log().info(config_message)

def _run_server():
    '''
    Runs the server (in production WSGI mode or in debug mode as determined by the RUN_WSGI_SERVER
    config flag)
    '''
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

def run(**kwargs):
    '''Parses configuration and runs the server'''
    _parse_config(kwargs)
    _run_server()

def test_run(username, password, **kwargs):
    '''Same as run, except that it also creates a user. Useful for testing.'''
    _parse_config(kwargs)
    memdam.server.admin.create_archive(username, password)
    _run_server()

def read_commandline_args():
    '''
    :returns: a mapping from key to value for the arguments defined on the commandline
    :rtype: dict(string, string)
    '''
    parser = argparse.ArgumentParser(description='Run the chronographer server.')
    parser.add_argument('--port', dest='LISTEN_PORT', type=int,
                        help='the port on which to listen')
    parser.add_argument('--host', dest='LISTEN_ADDRESS', type=str,
                        help='the ip address on which to listen')
    parser.add_argument('--wsgi', dest='RUN_WSGI_SERVER', type=bool,
                        help='if present, runs wsgi server for production, otherwise, runs in debug')
    parser.add_argument('--config', dest='CONFIG_FILE', type=str,
                        help='the path to a file with additional configuration')
    parser.add_argument('--db', dest='DATABASE_FOLDER', type=str,
                        help='the folder where the databases should be stored')
    parser.add_argument('--blobs', dest='BLOBSTORE_FOLDER', type=str,
                        help='the folder where the blobs should be stored')
    #hack for ipython admin interface:
    argv = sys.argv
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--')+1:]
    else:
        argv = argv[1:]
    args = parser.parse_args(argv)
    defined_args = select(lambda (k, v): v != None, vars(args))
    return defined_args

def run_as_script():
    '''Parses commandline arguments, converting them into the appropriate config variables'''
    run(**read_commandline_args())

if __name__ == '__main__':
    run_as_script()
