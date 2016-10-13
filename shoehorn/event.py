class Event(dict):

    def __repr__(self):
        parts = ', '.join(str(k)+'='+str(v) for (k, v) in sorted(self.items()))
        return 'Event('+parts+')'
