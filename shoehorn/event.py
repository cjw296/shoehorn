from collections import OrderedDict

from shoehorn.compat import text_types


class Event(OrderedDict):

    def serialize(self, exclude_keys=frozenset(),
                  join=', '.join, kw='=', quote=repr):
        return join(str(k)+kw+quote(v) for (k, v) in self.items()
                    if k not in exclude_keys)

    def extract_newline_values(self, exclude_keys=frozenset(),
                               prefix='\n', kw=':\n'):
        exclude = set(exclude_keys)
        parts = []
        for k, v in self.items():
            if k not in exclude and isinstance(v, text_types) and '\n' in v:
                parts.append(prefix+k+kw+v)
                exclude.add(k)
        return exclude, ''.join(parts)

    def __repr__(self):
        return 'Event('+self.serialize()+')'
