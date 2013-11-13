
"""
Saves and loads all events from the sqlite database
"""

import sqlite3

class TimeSeriesDatabase(object):
    """
    Simple storage scheme for all events of a particular type from a particular device.
    """
    
    def __init__(self, db_file):
        self.db_file = db_file
        
    def search_by_time(self, start_time, end_time):
        """search for events in a time range"""
        raise NotImplementedError
    
    #TODO: how exactly does text search work with FTS4? How many results will be returned? An iterator?
    def search_by_text(self, keywords):
        """search for events that best match a set of keywords"""
        raise NotImplementedError
    
    def store_events(self, events):
        """save a list of Events. Note that there is probably no way to ever delete events, and that no two events can happen at exaclty the same time.
        Overwriting an existing event should probably be an error, though you're welcome to write historical events.
        Hmm, I guess overwriting historical ones is fine then--maybe we got corrected data"""
        connection = sqlite3.connect(self.db_file, isolation_level=sqlite3.EXCLUSIVE)
        #where to hook up adapters?
        #verify that the table we're about to insert into has the correct columns
        #if not, add the required columns
        #and add their indices
        #finally, assemble inserts and execute
        