from __future__ import print_function

import re
from os.path import expanduser

from ..compat import text_types, Unicode
from ..event import Event
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


class EncodedWrite(object):

    def write(self, *parts):
        parts = [p.encode(self.encoding, errors='replace')
                 if isinstance(p, Unicode) else p
                 for p in parts]
        parts.append(b'\n')
        self.stream.write(b''.join(parts))


class JSON(Serializer):

    def __init__(self, stream, serialize=dump):
        self._make_stream(stream)
        self.serialize = serialize

    def __call__(self, event):
        self.serialize(event, self.stream, default=str)


class LTSV(EncodedWrite, Serializer):
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
        self.write(event.serialize(
            self.label_sep, self.item_sep.join, quote=self.quote
        ))


class Human(EncodedWrite, Serializer):

    prefix_pattern = re.compile('(?<={)[^:!}]+')
    prefix_bad_pattern = re.compile('{\d*(?:[:!].*)?}')
    only = None

    def __init__(self, stream, prefix='', ignore=None, only=None,
                 encoding='utf-8'):
        self._make_stream(stream)
        bad_prefix = self.prefix_bad_pattern.findall(prefix)
        if bad_prefix:
            raise AssertionError('bad prefix templating: {}'.format(
                ', '.join(bad_prefix)
            ))
        self.prefix = prefix
        self.exclude_keys = set(self.prefix_pattern.findall(prefix))
        if ignore:
            self.exclude_keys.update(ignore)
        if only:
            self.only = set(only)
        self.encoding = encoding

    def __call__(self, event):
        if self.only is not None:
            event = Event((k, v) for (k, v) in event.items()
                          if k in self.only)
        self.write(
            self.prefix.format(**event),
            event.serialize(exclude_keys=self.exclude_keys),
        )
