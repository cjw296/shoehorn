from unittest import TestCase

from testfixtures import compare

from shoehorn.event import Event


class TestEvent(TestCase):

    def test_repr(self):
        compare(repr(Event(y=1, x=2)), expected="Event(x=2, y=1)")

    def test_str(self):
        compare(str(Event(x=1, y=2)), expected="Event(x=1, y=2)")
