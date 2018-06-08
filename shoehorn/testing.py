from collections import deque

from shoehorn import logging


class TestTarget(object):

    __test__ = False

    #: .. note:: This isn't used during handling of events,
    #            it's only here for testing setting and un-setting
    #            error handlers.
    error_target = None

    def __init__(self, propagate=False):
        self.events = []
        self.propagate = propagate

    def __call__(self, event):
        self.events.append(event)
        if self.propagate:
            return event


class Capture(object):

    def __init__(self, stack):
        self._targets = deque()
        self.events = []
        self.stack = stack

    @property
    def targets(self):
        # don't include our own test target
        return list(self._targets)[:-1]

    def error_target(self, event):
        raise event['exception']

    def start(self):
        # vars is just a view, so need to take a copy:
        self.existing = dict(vars(self.stack))
        self.stack.targets = self._targets
        self.stack.error_target = self.error_target
        self.stack.error_target_installed = []
        target = TestTarget()
        self.stack.push(target)
        self.events = target.events

    def stop(self):
        targets = []
        while self._targets:
            targets.append(self.stack.pop())
        for attr, value in self.existing.items():
            setattr(self.stack, attr, value)
        # for later inspection
        self._targets = targets

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


try:
    import pytest
except ImportError:  # pragma: no cover
    pass
else:
    @pytest.fixture()
    def capture():
        with Capture(logging) as capture:
            yield capture
