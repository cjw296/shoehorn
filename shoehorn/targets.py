class Stack(object):

    def __init__(self):
        self.targets = []

    def push(self, *targets):
        self.targets.extend(targets)

    def __call__(self, event):
        for target in self.targets:
            event = target(event)
            if event is None:
                break


class Layer(object):

    def __init__(self, *targets, propagate=False):
        self.targets = []
        self.targets.extend(targets)
        self.propagate = propagate

    def add(self, target):
        self.targets.append(target)

    def __call__(self, event):
        for target in self.targets:
            target(event)
        if self.propagate:
            return event
