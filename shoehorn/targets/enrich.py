from datetime import datetime
from traceback import format_exception, format_stack
import sys

from ..compat import PY3

#: A constant specifying that the timestamp should be logged in UTC.
UTC = 'utc'


class AddTimestamp(object):

    tz = None
    now = datetime.now

    def __init__(self, key='timestamp', tz=None, format=None):
        """
        :param key: string specifying the key to add to the event

        :param tz:
          The timezone in which to add the timestamp.
          Can be a :class:`~datetime.tzinfo` object, the :attr:`UTC`
        """
        self.key = key
        if tz == UTC:
            self.now = datetime.utcnow
        else:
            self.tz = tz
        self.format = format

    def __call__(self, event):
        if self.tz is None:
            now = self.now()
        else:
            now = self.now(self.tz)
        if self.format is None:
            timestamp = now.isoformat()
        else:
            timestamp = now.strftime(self.format)
        event[self.key] = timestamp
        return event


def add_traceback(event):
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
