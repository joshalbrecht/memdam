
import os
import sys
import tempfile

#TODO: evaluate this for security issues. Should probably be careful about user and permissions when writing data.
def make_temp_path():
    """
    :returns: a temporary file name
    :rtype: string
    """
    return tempfile.mktemp()

def is_windows():
    return os.name == 'nt'

def is_osx():
    return sys.platform == 'darwin'

def is_installed():
    return getattr(sys, 'frozen', '') != ''

