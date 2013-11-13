
"""
Maintains a mapping from device/data_type pairs to the actual time series that is stored
"""

class UserData(object):
    def __init__(self, data_folder):
        self.data_folder = data_folder
        
    def series(self, device_name, data_type):
        """Check that the folder exists and return the TimeSeriesDatabase"""
        raise NotImplementedError
    
