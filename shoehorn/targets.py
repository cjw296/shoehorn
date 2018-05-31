class Stack(object):

    def __init__(self):
        self.targets = []

    def push(self, *handlers):
        self.targets.extend(handlers)

    def __call__(self, event):
        for target in self.targets:
            event = target(event)
            if event is None:
                break


class Layer(object):

    def __init__(self, *handlers, propagate=False):
        self.targets = []
        self.targets.extend(handlers)
        self.propagate = propagate

    def add(self, handler):
        self.targets.append(handler)

    def __call__(self, event):
        for target in self.targets:
            target(event)
        if self.propagate:
            return event
