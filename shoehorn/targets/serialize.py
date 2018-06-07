from os.path import expanduser
from ..compat import text_types

try:
    from rapidjson import dump
except ImportError:
    from json import dump


class JSON(object):

    def __init__(self, stream, serialize=dump):
        self.serialize = serialize
        if isinstance(stream, text_types):
            stream = open(expanduser(stream), 'a')
        self.stream = stream

    def __call__(self, event):
        self.serialize(event, self.stream, default=str)

    def close(self):
        self.stream.close()
