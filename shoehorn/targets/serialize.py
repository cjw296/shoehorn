from __future__ import print_function

from os.path import expanduser
import re

from ..compat import text_types, Unicode, PY2
from ..event import Event
try:
    from rapidjson import dumps
except ImportError:
    from json import dumps


class Serializer(object):

    encoding = 'utf-8'

    def __init__(self, stream):
        if isinstance(stream, text_types):
            stream = open(expanduser(stream), 'ab')
        self.stream = stream

    def close(self):
        self.stream.close()

    def write(self, *parts):
        parts = [p.encode(self.encoding, errors='replace')
                 if isinstance(p, Unicode) else p
                 for p in parts]
        parts.append(b'\n')
        self.stream.write(b''.join(parts))


class JSON(Serializer):

    def __call__(self, event):
        try:
            text = dumps(event, default=str)
        except UnicodeDecodeError:
            # slow path...
            if PY2:
                safe_event = Event()
                for k, v in event.items():
                    if isinstance(v, str):
                        try:
                            v = v.decode(self.encoding)
                        except UnicodeDecodeError:
                            v = repr(v)
                    safe_event[k] = v
            else:
                safe_event = Event(
                    (k, repr(v) if isinstance(v, bytes) else v)
                    for (k, v) in event.items()
                )
            text = dumps(safe_event, default=str)
        self.stream.write(text.encode(self.encoding))


class LTSV(Serializer):
    # http://ltsv.org/

    def __init__(self, stream, label_sep=':', item_sep='\t', encoding='utf-8'):
        super(LTSV, self).__init__(stream)
        assert set(len(sep) for sep in (label_sep, item_sep)) == {1}, \
            'separators can only be one character is length'
        assert ' ' not in (label_sep, item_sep), \
            'space cannot be used as a separator'
        self.label_sep = label_sep
        self.item_sep = item_sep
        self.sub = re.compile('['+'\n\r'+label_sep+item_sep+']').sub
        self.encoding = encoding

    def quote(self, item):
        try:
            item = Unicode(item)
        except UnicodeDecodeError:
            item = repr(item)
        return self.sub(' ', item)

    def __call__(self, event):
        self.write(event.serialize(
            self.label_sep, self.item_sep.join, quote=self.quote
        ))


class Human(Serializer):

    prefix_pattern = re.compile('(?<={)[^:!}]+')
    prefix_bad_pattern = re.compile('{\d*(?:[:!].*)?}')
    only = None

    def __init__(self, stream, prefix='', ignore=None, only=None,
                 encoding='utf-8'):
        super(Human, self).__init__(stream)
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
