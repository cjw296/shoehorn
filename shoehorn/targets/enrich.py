from sys import exc_info
from traceback import format_exception, format_stack

from ..compat import PY3


def add_traceback(event):
    exception = event.get('exception')
    wants_tb = event.pop('exc_info', False)

    if exception is not None or wants_tb:
        type_, value, tb  = None, None, None

        if isinstance(exception, BaseException):
            type_, value = exception.__class__, exception
            if PY3:
                tb = exception.__traceback__
        elif wants_tb:
            type_, value, tb = exc_info()

        if type_ is None:
            parts = format_stack()
        else:
            parts = format_exception(type_, value, tb)

        event['traceback'] = ''.join(parts).strip('\n')

    return event
