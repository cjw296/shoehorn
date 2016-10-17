class Event(dict):

    def serialize(self, kw='=', join=', '.join, quote=repr,
                  exclude_keys=frozenset()):
        return join(str(k)+kw+quote(v) for (k, v) in sorted(self.items())
                    if k not in exclude_keys)

    def __repr__(self):
        return 'Event('+self.serialize()+')'
