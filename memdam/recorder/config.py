
import os
import json
import platform

# pylint: disable=W0401,W0622,W0614
from funcy import *

import memdam.common.utils

class Config(object):
    """
    Loads a json configuration.

    This class IS IMMUTABLE. Configuration should NOT be changed at runtime!
    """

    def __init__(self, filename=None, **kwargs):
        self.filename = filename
        self.data = None
        if os.path.exists(filename):
            with open(filename, 'rb') as infile:
                self.data = json.loads(infile.read())
        if self.data == None:
            self.data = {}
        for key, value in kwargs.iteritems():
            self.data[key] = value

    def get(self, key):
        return self.data[key]

    def save(self):
        with open(self.filename, 'wb') as outfile:
            outfile.write(self.to_json())

    def to_json(self):
        return json.dumps(self.data, sort_keys=True, indent=4, separators=(',', ': '))

    def format_for_log(self):
        def password_filter(data):
            '''replace passwords with ****'''
            key, value = data
            if 'password' in key:
                value = '*****'
            return (key, value)
        filtered_data = walk(password_filter, self.data)
        return json.dumps(filtered_data, sort_keys=True, indent=4, separators=(',', ': '))

def get_default_config(filename, collectors):
    """
    Note: this will/should probably return different values depending on if this is running
    from an installation or from a debug environment.

    :returns: the default configuration for a new installation. Note that username and password
    keys will not be set, but everything else required for running should be set.
    :rtype: memdam.recorder.config.Config
    """
    data_folder = os.path.join(os.path.join(os.path.expanduser('~'), u'.chronographer'), u'data')
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    device_id = platform.node()
    server_url = u'http://127.0.0.1:5000/api/v1/'
    if memdam.common.utils.is_installed():
        server_url = u'http://ec2-54-201-240-100.us-west-2.compute.amazonaws.com:5000/api/v1/'
    return Config(filename, data_folder=data_folder, device_id=device_id, server_url=server_url, log_level='DEBUG', collectors=collectors)
