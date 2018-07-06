from sys import exc_info

import pytest
from pytz import timezone
from testfixtures import StringComparison as S, compare, test_datetime, Replace

from shoehorn.compat import PY3
from shoehorn.targets.enrich import add_traceback, AddTimestamp, UTC


class TestAddTimestamp(object):

    @pytest.fixture(autouse=True)
    def datetime(self):
        dt = test_datetime(tzinfo=timezone('US/Eastern'))
        with Replace('shoehorn.targets.enrich.datetime', dt):
            yield dt

    def test_simple(self):
        event = AddTimestamp()({})
        compare(event, expected={'timestamp': '2001-01-01T00:00:00'})

    def test_key(self):
        event = AddTimestamp(key='foo')({})
        compare(event, expected={'foo': '2001-01-01T00:00:00'})

    def test_utc(self):
        event = AddTimestamp(tz=UTC())({})
        compare(event, expected={'timestamp': '2001-01-01T05:00:00+00:00'})

    def test_tzinfo(self):
        event = AddTimestamp(tz=timezone('Australia/Canberra'))({})
        compare(event, expected={'timestamp': '2001-01-01T16:00:00+11:00'})

    def test_format_string(self):
        event = AddTimestamp(format='%Y-%m-%d %H:%M')({})
        compare(event, expected={'timestamp': '2001-01-01 00:00'})


exception_with_traceback = S('(?s)^Traceback \(most recent call last\):'
                             '.+'
                             'Exception: boom!')

if PY3:
    expected_traceback = exception_with_traceback
else:
    expected_traceback = 'Exception: boom!'


class TestExtractTraceback(object):

    def test_from_exception(self):
        try:
            raise Exception('boom!')
        except Exception as e:
            event = add_traceback({'exception': e})

            compare(event, expected={
                'traceback': expected_traceback
            })

    def test_explicit_exception(self):
        try:
            raise Exception('boom!')
        except Exception as e_:
            e = e_
        try:
            raise Exception('wut?')
        except:
            event = add_traceback({'exception': e})
            compare(event, expected={
                'traceback': expected_traceback
            })

    def test_explicit_exception_no_traceback(self):
        e = Exception('boom!')
        event = add_traceback({'exception': e})
        compare(event, expected={
            'traceback': S('Exception: boom!')
        })

    def test_exc_info_true_with_exception(self):
        try:
            raise Exception('boom!')
        except Exception:
            event = add_traceback({'exc_info': True})

            compare(event, expected={
                'traceback': S('(?s)^Traceback \(most recent call last\):'
                               '.+'
                               'Exception: boom!$')
            })

    def test_exc_info_true_no_exception(self):
        event = add_traceback({'exc_info': True})
        compare(event, expected={
            'traceback': S('(?s)^ *File'
                           '.+'
                           'parts = format_stack\(\)$')
        })

    def test_exc_info_from_sys(self):
        try:
            raise Exception('boom!')
        except:
            event = add_traceback({'exc_info': exc_info()})

            compare(event, expected={
                'traceback': exception_with_traceback
            })

    def test_exception_but_no_logging_wanted(self):
        try:
            raise Exception('boom!')
        except Exception as e:
            pass
        event = add_traceback({})
        compare(event, expected={})
