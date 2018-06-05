from testfixtures import compare, ShouldRaise

from shoehorn import Stack
from shoehorn.testing import TestTarget, Capture


class TestTestTarget(object):

    def test_propagate(self):
        target = TestTarget(propagate=True)
        event = {}
        result = target(event)
        assert result is event

    def test_no_propagate(self):
        target = TestTarget()
        event = {}
        result = target(event)
        assert result is None

    def test_recording(self):
        target = TestTarget()
        event = {}
        target(event)
        assert target.events[0] is event
        assert tuple(target.events) == (event, )


class TestCapture(object):

    def test_start_stop(self):
        stack = Stack()
        compare(stack.targets, expected=[])
        capture = Capture(stack)
        capture.start()

        stack('event 1')
        t = TestTarget()
        stack.push(t)
        stack('event 2')

        capture.stop()
        compare(capture.events, expected=['event 1'])
        compare(capture.targets, expected=[t], recursive=False)
        compare(t.events, expected=['event 2'])
        compare(stack.targets, expected=[], recursive=False)

    def test_context_manager(self):
        stack = Stack()
        compare(stack.targets, expected=[])

        with Capture(stack) as capture:
            stack('event 1')
            t = TestTarget()
            stack.push(t)
            stack('event 2')

        compare(capture.events, expected=['event 1'])
        compare(capture.targets, expected=[t], recursive=False)
        compare(t.events, expected=['event 2'])
        compare(stack.targets, expected=[], recursive=False)

    def test_pushed_with_existing(self):
        stack = Stack()
        t1 = TestTarget()
        t2 = TestTarget()
        stack.push(t1, t2)
        compare(stack.targets, expected=[t1, t2], recursive=False)
        capture = Capture(stack)
        capture.start()
        stack.push(TestTarget())
        stack.push(TestTarget())
        capture.stop()
        compare(stack.targets, expected=[t1, t2], recursive=False)

    def test_pushed_stack_has_error_target(self):
        et = TestTarget()
        stack = Stack(error_target=et)
        capture = Capture(stack)
        capture.start()
        t = TestTarget()
        stack.push(t)
        assert t.error_target.__func__ is capture.error_target.__func__
        capture.stop()
        assert t.error_target is None

    def test_error(self):
        stack = Stack()
        capture = Capture(stack)
        capture.start()

        e = Exception("boom!")

        def boom(event):
            raise e

        stack.push(boom)
        with ShouldRaise(e):
            stack('event')
