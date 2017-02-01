from unittest import TestCase

from testfixtures import compare

from shoehorn.compat import PY36
from shoehorn.event import Event


class TestEvent(TestCase):

    def test_repr(self):
        compare(repr(Event([('x', '2'), ('y', 1)])),
                expected="Event(x='2', y=1)")

    def test_str(self):
        compare(str(Event([('x', 1), ('y', 2)])),
                expected="Event(x=1, y=2)")

    if PY36:

        def test_repr_kw_ordered(self):
            compare(repr(Event(x='2', y=1)), expected="Event(x='2', y=1)")

        def test_str_kw_ordered(self):
            compare(str(Event(x=1, y=2)), expected="Event(x=1, y=2)")
