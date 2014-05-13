
import os
import shutil
import json

class StateStore(object):
    """
    Stores a json object of state into a file.

    Tries pretty hard to make the set_state an atomic operation.
    """

    #TODO: should not do raw file name manipulation. Should probably all exist in some nice little container that can be encrypted, etc
    def __init__(self, json_file):
        self._json_file = json_file
        self._temp_file = self._json_file + ".tmp"
        #fix unclean shutdown
        if not os.path.exists(self._json_file):
            if os.path.exists(self._temp_file):
                os.rename(self._temp_file, self._json_file)

    def get_state(self):
        """
        :returns: the current state
        :rtype: dict
        """
        if not os.path.exists(self._json_file):
            return {}
        with open(self._json_file, 'rb') as infile:
            return json.load(infile)

    def set_state(self, data):
        """
        Actually writes out to another file and then moves the file, to try to prevent corruption
        in the case of an unclean shutdown.

        :param data: the current state to save
        :type  data: dict
        """
        with open(self._temp_file, 'wb') as outfile:
            json.dump(data, outfile)
        if os.path.exists(self._json_file):
            os.remove(self._json_file)
        shutil.move(self._temp_file, self._json_file)
