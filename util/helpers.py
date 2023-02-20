import urllib.parse as urlparse
from datetime import datetime
import random


def validateURL(url):
    """[Checking if string is ur]

    Arguments:
        url {[string]} -- [URL]

    Returns:
        [Boolean]
    """
    return urlparse.urlparse(url).scheme != ""


def _epoch_utc_to_datetime(epoch_utc):
    """
    Helper function for converting epoch timestamps (as stored in JWTs) into
    python datetime objects (which are easier to use with sqlalchemy).
    """
    return datetime.fromtimestamp(epoch_utc)


def generateBoardColor():
    secure_random = random.SystemRandom()
    colors = ['#E0BBE4', '#957DAD', '#D291BC', '#FEC8D8', '#FFDFD3', '#EF4056', '#00CB77', '#1CB0A8']
    return secure_random.choice(colors)
