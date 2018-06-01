from .event import Event


MARKER = object()


def handle_error(target, exception, event):
    if target is not None:
        target(Event((
            ('exception', exception),
            ('event', event)
        )))


class Stack(object):

    def __init__(self, error_target=None):
        self.targets = []
        self.error_target = error_target

    def push(self, *targets):
        self.targets.extend(targets)
        if self.error_target is not None:
            for target in targets:
                if getattr(target, 'error_target', MARKER) is None:
                    target.error_target = self.error_target

    def __call__(self, event):
        try:
            for target in self.targets:
                event = target(event)
                if event is None:
                    break
        except Exception as exception:
            handle_error(self.error_target, exception, event)


class Layer(object):

    def __init__(self, *targets, propagate=False, error_target=None):
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
