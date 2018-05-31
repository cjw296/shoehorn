class TestTarget(object):

    def __init__(self, propagate=False):
        self.events = []
        self.propagate = propagate

    def __call__(self, event):
        self.events.append(event)
        if self.propagate:
            return event
