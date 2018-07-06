from types import TracebackType

from testfixtures import Comparison as C, compare

from shoehorn.event import Event
from shoehorn.targets.compose import Stack, Layer
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

    def test_two_constructor(self):
        t1 = TestTarget(propagate=True)
        t2 = TestTarget()
        s = Stack(t1, t2)
        s.push()
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

    def test_targets_ordering(self):
        t1 = TestTarget()
        t2 = TestTarget(propagate=False)
        s = Stack()
        s.push(t1)
        s.push(t2)
        s('event')
        compare(t1.events, expected=[])
        compare(t2.events, expected=['event'])

    def test_replace_event(self):
        def handle(event):
            return 'something else'
        t = TestTarget()
        s = Stack()
        s.push(handle, t)
        s('event')
        compare(t.events, expected=['something else'])

    def test_filter(self):
        t = TestTarget()
        s = Stack(
            lambda event: event['foo'] == 'bar',
            t
        )
        s({'foo': 'bar'})
        s({'foo': 'baz'})
        compare(t.events, expected=[{'foo': 'bar'}])

    def test_error_with_handler(self):
        e = Exception('boom!')
        def handle(event):
            raise e
        t1 = TestTarget()
        t2 = TestTarget()
        s = Stack(error_target=t1)
        s.push(handle, t2)
        s('event')
        compare(t1.events, expected=[Event(
            exc_info=(Exception, e, C(TracebackType)),
            event="'event'"
        )])
        # with a stack, we don't keep going after an error:
        compare(t2.events, expected=[])

    def test_error_without_handler(self):
        def handle(event):
            raise Exception('boom!')
        t = TestTarget()
        s = Stack()
        s.push(handle, t)
        s('event')
        # with a stack, we don't keep going after an error:
        compare(t.events, expected=[])

    def test_set_error_handler_on_push(self):
        t = TestTarget()
        s = Stack(error_target='foo')
        s.push(t)
        assert t.error_target == 'foo'

    def test_leave_existing_error_target(self):
        t = TestTarget()
        t.error_target = 'bar'
        s = Stack(error_target='foo')
        s.push(t)
        assert t.error_target == 'bar'

    def test_pop(self):
        s = Stack()
        target1 = object()
        target2 = object()
        s.push(target1, target2)
        assert list(s.targets) == [target1, target2]
        returned = s.pop()
        assert returned is target1
        returned = s.pop()
        assert returned is target2
        assert list(s.targets) == []

    def test_pop_error_target(self):
        error_target = object()
        s = Stack(error_target=error_target)
        target = TestTarget()
        s.push(target)
        assert target.error_target == error_target
        s.pop()
        assert target.error_target is None

    def test_other_error_target(self):
        error_target1 = object()
        error_target2 = object()
        s = Stack(error_target=error_target1)
        target = TestTarget()
        target.error_target = error_target2
        s.push(target)
        assert target.error_target == error_target2
        s.pop()
        assert target.error_target == error_target2


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

    def test_error_with_handler(self):
        e = Exception('boom!')
        def handle(event):
            raise e
        t1 = TestTarget()
        t2 = TestTarget()
        l = Layer(handle, t2, error_target=t1)
        l('event')
        compare(t1.events, expected=[Event(
            exc_info=(Exception, e, C(TracebackType)),
            event="'event'"
        )])
        # with a layer, we do keep going after an error:
        compare(t2.events, expected=['event'])

    def test_error_without_handler(self):
        def handle(event):
            raise Exception('boom!')
        t = TestTarget()
        l = Layer(handle, t)
        l('event')
        # with a stack, we do keep going after an error:
        compare(t.events, expected=['event'])
