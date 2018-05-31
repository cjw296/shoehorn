from shoehorn.testing import TestTarget


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


