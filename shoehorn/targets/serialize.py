from __future__ import print_function

import re
from os.path import expanduser

from ..compat import text_types, Unicode

try:
    from rapidjson import dump
except ImportError:
    from json import dump


class Serializer(object):

    def _make_stream(self, stream):
        if isinstance(stream, text_types):
            stream = open(expanduser(stream), 'ab')
        self.stream = stream

    def close(self):
        self.stream.close()


class JSON(Serializer):

    def __init__(self, stream, serialize=dump):
        self._make_stream(stream)
        self.serialize = serialize

    def __call__(self, event):
        self.serialize(event, self.stream, default=str)


class LTSV(Serializer):
    # http://ltsv.org/

    def __init__(self, stream, label_sep=':', item_sep='\t', encoding='utf-8'):
        assert set(len(sep) for sep in (label_sep, item_sep)) == {1}, \
            'separators can only be one character is length'
        assert ' ' not in (label_sep, item_sep), \
            'space cannot be used as a separator'
        self._make_stream(stream)
        self.label_sep = label_sep
        self.item_sep = item_sep
        self.sub = re.compile('['+'\n\r'+label_sep+item_sep+']').sub
        self.encoding = encoding

    def quote(self, item):
        return self.sub(' ', Unicode(item))

    def __call__(self, event):
        text = event.serialize(
            self.label_sep, self.item_sep.join, quote=self.quote
        )
        if isinstance(text, Unicode):
            text = text.encode(self.encoding, errors='replace')
        self.stream.write(text)
        self.stream.write(b'\n')
