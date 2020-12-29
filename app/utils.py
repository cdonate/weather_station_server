import datetime
import csv
import io


def parse_csv(csv_byte):
    reader_list = csv.DictReader(io.StringIO(csv_byte.decode("utf-8")))
    return list(reader_list)


def round_time(dt, date_delta=datetime.timedelta(minutes=15)):
    """Round a datetime object to a multiple of a timedelta
    dt : datetime.datetime object, default now.
    dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
            Stijn Nevens 2014 - Changed to use only datetime objects as variables
    """
    round_to = date_delta.total_seconds()

    seconds = (dt - dt.min).seconds
    # // is a floor division, not a comment on following line:
    rounding = (seconds + round_to / 2) // round_to * round_to
    return dt + datetime.timedelta(0, rounding - seconds, -dt.microsecond)
