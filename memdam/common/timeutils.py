
"""
Contains some helper functions related to time
"""

import datetime
import pytz

def now():
    """
    Use this in preference to raw date times for the following advantages:
    - Stop forgetting to use UTC everywhere
    - Allow debugging of tricky time-based bugs
    :return: the current time.
    """
    return pytz.timezone('UTC').localize(datetime.datetime.utcnow())
