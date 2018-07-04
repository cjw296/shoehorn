from __future__ import print_function

from io import open
from os.path import expanduser
import re

from ..compat import text_types, Unicode, PY2
from ..event import Event
try:
    from rapidjson import dumps
except ImportError:
    from json import dumps


class Serializer(object):

    def __init__(self, stream):
        if isinstance(stream, text_types):
            stream = open(expanduser(stream), 'a', errors='backslashreplace')
        self.stream = stream

    def close(self):
        self.stream.close()

    def write(self, *parts):
        self.stream.write(u''.join(parts)+'\n')
        self.stream.flush()


class JSON(Serializer):

    def __call__(self, event):
        try:
            text = dumps(event, default=str)
        except UnicodeDecodeError:
            # slow path...
            if PY2:
                safe_event = Event()
                for k, v in event.items():
                    if self.stream.encoding:
                        encoding = (self.stream.encoding,)
                    else:
                        encoding = ()
                    if isinstance(v, str):
                        try:
                            v = v.decode(*encoding)
                        except UnicodeDecodeError:
                            v = repr(v)
                    safe_event[k] = v
            else:
                safe_event = Event(
                    (k, repr(v) if isinstance(v, bytes) else v)
                    for (k, v) in event.items()
                )
            text = dumps(safe_event, default=str)
        if isinstance(text, bytes):
            text = text.decode('utf8')
        self.stream.write(text)


class LTSV(Serializer):
    # http://ltsv.org/

    def __init__(self, stream, label_sep=':', item_sep='\t'):
        super(LTSV, self).__init__(stream)
        assert set(len(sep) for sep in (label_sep, item_sep)) == {1}, \
            'separators can only be one character is length'
        assert ' ' not in (label_sep, item_sep), \
            'space cannot be used as a separator'
        self.label_sep = label_sep
        self.item_sep = item_sep
        self.sub = re.compile('['+'\n\r'+label_sep+item_sep+']').sub

    def quote(self, item):
        try:
            item = Unicode(item)
        except UnicodeDecodeError:
            item = repr(item)
        return self.sub(' ', item)

    def __call__(self, event):
        self.write(event.serialize(
            kw=self.label_sep, join=self.item_sep.join, quote=self.quote
        ))


class Human(Serializer):

    prefix_pattern = re.compile('(?<={)[^:!}]+')
    prefix_bad_pattern = re.compile('{\d*(?:[:!].*)?}')
    only = None

    def __init__(self, stream, prefix='', ignore=None, only=None):
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

    def __call__(self, event):
        if self.only is not None:
            event = Event((k, v) for (k, v) in event.items()
                          if k in self.only)
        exclude, post = event.extract_newline_values(self.exclude_keys)
        self.write(
            self.prefix.format(**event),
            event.serialize(exclude),
            post,
        )
