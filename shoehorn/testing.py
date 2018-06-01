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
