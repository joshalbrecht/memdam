
import os
import sys
import tempfile

import memdam

#TODO: evaluate this for security issues. Should probably be careful about user and permissions when writing data.
@memdam.tracer
def make_temp_path():
    """
    :returns: a temporary file name
    :rtype: string
    """
    return tempfile.mktemp()

@memdam.tracer
def is_windows():
    return os.name == 'nt'

@memdam.tracer
def is_osx():
    return sys.platform == 'darwin'

@memdam.tracer
def is_installed():
    return getattr(sys, 'frozen', '') != ''
