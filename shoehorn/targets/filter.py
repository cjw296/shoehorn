import re

from shoehorn.event import Event


class RemoveKeys(object):

    def __init__(self, *keys):
        self.keys = keys

    def __call__(self, event):
        for key in self.keys:
            event.pop(key, None)
        return event


class RemoveKeysByPattern(object):

    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def __call__(self, event):
        return Event((k, v) for (k, v) in event.items()
                     if not self.pattern.match(k))
