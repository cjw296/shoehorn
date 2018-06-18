from testfixtures import StringComparison as S, compare

from shoehorn.compat import PY3
from shoehorn.targets.enrich import add_traceback


if PY3:
    expected_traceback = S('(?s)^Traceback \(most recent call last\):'
                           '.+'
                           'Exception: boom!')
else:
    expected_traceback = 'Exception: boom!'


class TestExtractTraceback(object):

    def test_from_exception(self):
        try:
            raise Exception('boom!')
        except Exception as e:
            event = add_traceback({'exception': e})

            compare(event, expected={
                'exception': e,
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
                'exception': e,
                'traceback': expected_traceback
            })

    def test_explicit_exception_no_traceback(self):
        e = Exception('boom!')
        event = add_traceback({'exception': e})
        compare(event, expected={
            'exception': e,
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

    def test_exception_but_no_logging_wanted(self):
        try:
            raise Exception('boom!')
        except Exception as e:
            pass
        event = add_traceback({})
        compare(event, expected={})

