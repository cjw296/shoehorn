from testfixtures import compare

from shoehorn.targets import Stack, Layer
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


class TestLayer(object):

    def test_empty(self):
        Layer()('event')

    def test_one(self):
        t = TestTarget()
        l = Layer()
        l.add(t)
        l('event')
        compare(t.events, expected=['event'])

    def test_two(self):
        t1 = TestTarget()
        t2 = TestTarget()
        l = Layer()
        l.add(t1)
        l.add(t2)
        l('event')
        compare(t1.events, expected=['event'])
        compare(t2.events, expected=['event'])

    def test_replace_event(self):
        def handle(event):
            return 'something else'
        t = TestTarget()
        l = Layer()
        l.add(handle)
        l.add(t)
        l('event')
        compare(t.events, expected=['event'])

    def test_constructor(self):
        t1 = TestTarget()
        t2 = TestTarget()
        l = Layer(t1, t2)
        l('event')
        compare(t1.events, expected=['event'])
        compare(t2.events, expected=['event'])

    def test_propagate(self):
        l = Layer(propagate=True)
        result = l('event')
        assert result == 'event'

    def test_no_propagate(self):
        l = Layer()
        result = l('event')
        assert result is None
