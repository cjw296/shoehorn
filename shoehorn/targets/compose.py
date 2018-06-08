from collections import deque
from itertools import chain

from ..event import Event


MARKER = object()


def handle_error(target, exception, event):
    if target is not None:
        target(Event((
            ('exception', exception),
            ('event', event)
        )))


class Stack(object):

    def __init__(self, *targets, **kw):
        error_target = kw.pop('error_target', None)
        assert not kw, 'only error_target is a keyword parameter'
        self.targets = deque()
        self.error_target = error_target
        self.error_target_installed = []
        self.push(*targets)

    def push(self, *targets):
        self.targets.extendleft(reversed(targets))
        if self.error_target is not None:
            for target in targets:
                if getattr(target, 'error_target', MARKER) is None:
                    target.error_target = self.error_target
                    self.error_target_installed.append(target)

    def pop(self):
        target = self.targets.popleft()
        if target in self.error_target_installed:
            target.error_target = None
            self.error_target_installed.remove(target)
        return target

    def __call__(self, event):
        try:
            for target in self.targets:
                event = target(event)
                if event is None:
                    break
        except Exception as exception:
            handle_error(self.error_target, exception, event)


class Layer(object):

    def __init__(self, *targets, **kw):
        propagate = kw.pop('propagate', False)
        error_target = kw.pop('error_target', None)
        assert not kw, 'only propagate and error_target are keyword parameters'
        
        self.targets = []
        self.targets.extend(targets)
        self.propagate = propagate
        self.error_target = error_target

    def add(self, target):
        self.targets.append(target)

    def __call__(self, event):
        for target in self.targets:
            try:
                target(event)
            except Exception as exception:
                handle_error(self.error_target, exception, event)
        if self.propagate:
            return event
