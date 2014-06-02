
"""
Contains some helper functions related to time
"""

import time
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

def local_time_to_utc(unaware_time):
    """
    Converts an unaware time in the current computer timezone to UTC.
    Also accounts for it being daylight savings time or not during that date, eg, this datetime is what someone wrote down from a clock on that day.
    Assumes that the user has not changed their time zone inbetween.
    """
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    adjusted_time = unaware_time + datetime.timedelta(seconds=offset)
    return datetime.datetime(adjusted_time.year, adjusted_time.month, adjusted_time.day, adjusted_time.hour, adjusted_time.minute, adjusted_time.second, adjusted_time.microsecond, pytz.UTC)
