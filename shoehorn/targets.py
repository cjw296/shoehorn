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
