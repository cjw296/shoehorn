from testfixtures import compare

from shoehorn.targets import Stack
from shoehorn.testing import TestTarget


class TestStack(object):

    def test_empty(self):
        Stack()('event')

    def test_one(self):
        t = TestTarget()
        s = Stack()
        s.push(t)
        s('event')
        compare(t.events, expected=['event'])

    def test_two(self):
        t1 = TestTarget(propagate=True)
        t2 = TestTarget()
        s = Stack()
        s.push(t1, t2)
        s('event')
        compare(t1.events, expected=['event'])
        compare(t2.events, expected=['event'])

    def test_no_propagate(self):
        t1 = TestTarget(propagate=False)
        t2 = TestTarget()
        s = Stack()
        s.push(t1, t2)
        s('event')
        compare(t1.events, expected=['event'])
        compare(t2.events, expected=[])

    def test_replace_event(self):
        def handle(event):
            return 'something else'
        t = TestTarget()
        s = Stack()
        s.push(handle, t)
        s('event')
        compare(t.events, expected=['something else'])
