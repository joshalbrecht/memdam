
import os
import sys
import tempfile

import memdam

#TODO: also, this should be marked as deprecated and/or removed--it is unsafe, per the docstring.
#best way to replace would probably be to make a context that takes care of closing/deleting the file (and using with with:)
#TODO: evaluate this for security issues. Should probably be careful about user and permissions when writing data.
@memdam.vtrace()
def make_temp_path():
    """
    :returns: a temporary file name
    :rtype: string
    """
    return tempfile.mktemp()

@memdam.vtrace()
def is_windows():
    return os.name == 'nt'

@memdam.vtrace()
def is_osx():
    return sys.platform == 'darwin'

@memdam.vtrace()
def is_installed():
    return getattr(sys, 'frozen', '') != ''
