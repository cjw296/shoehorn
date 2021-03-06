from datetime import datetime, tzinfo, timedelta
from traceback import format_exception, format_stack
import sys

from ..compat import PY3


#: A simple UTC implementation so that you don't need :mod:`pytz`.
class UTC(tzinfo):
    # def tzname(self,**kwargs):
    #     return "UTC"
    def utcoffset(self, dt):
        return timedelta(0)
    def dst(self, dt):
        return timedelta(0)


class Timestamp(object):

    tz = None

    def __init__(self, key='timestamp', tz=None, format=None):
        """
        :param key: string specifying the key to add to the event

        :param tz:
          The timezone in which to add the timestamp, specified as a
          :class:`~datetime.tzinfo` instance.
          If not specified, the timestamp will be added in the local time with
          no timezone.
        """
        self.key = key
        self.tz = tz
        self.format = format

    def __call__(self, event):
        now = datetime.now(self.tz)
        if self.format is None:
            timestamp = now.isoformat()
        else:
            timestamp = now.strftime(self.format)
        event[self.key] = timestamp
        return event


def traceback(event):
    type_ = None
    value = event.pop('exception', None)
    tb = None

    exc_info = event.pop('exc_info', False)
    if isinstance(exc_info, bool):
        wants_tb = exc_info
    else:
        type_, ei_value, tb = exc_info
        value = ei_value if value is None else value
        wants_tb = True

    if value is not None or wants_tb:

        if isinstance(value, BaseException):
            type_, value = type(value), value
            if PY3:
                tb = value.__traceback__

        if wants_tb and not all((type_, value, tb)):
            # primarily because python 2's exceptions have no __traceback__
            ei_type, ei_value, ei_tb = sys.exc_info()
            type_ = ei_type if type_ is None else type_
            value = ei_value if value is None else value
            tb = ei_tb if tb is None else tb

        if type_ is None:
            parts = format_stack()
        else:
            parts = format_exception(type_, value, tb)

        event['traceback'] = ''.join(parts).strip('\n')

    return event
