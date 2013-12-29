
import tempfile

#TODO: evaluate this for security issues. Should probably be careful about user and permissions when writing data.
def make_temp_path():
    """
    :returns: a temporary file name
    :rtype: string
    """
    return tempfile.mktemp()
