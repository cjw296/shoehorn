from logging import getLogger, INFO, _nameToLevel

sentinel = object()


class StandardLibraryTarget(object):

    def __init__(self, default_level=INFO):
        self.default_level=default_level
        self.loggers = {}
        # do this late in case something adds more levels
        self.levels = {n.lower(): l for (n, l) in _nameToLevel.items()}

    def __call__(self, event):

        name = event.get('logger')
        if name not in self.loggers:
            self.loggers[name] = getLogger(name)
        logger = self.loggers[name]

        level = event.get('level', self.default_level)
        if not isinstance(level, int):
            level = self.levels.get(level, self.default_level)

        kwargs = {}
        for name in ('exc_info', 'stack_info'):
            if name in event:
                value = event.get(name, sentinel)
                if value is not sentinel:
                    kwargs[name] = value
        kwargs['extra'] = dict(shoehorn_event=event)

        logger.log(
            level,
            event.get('message'),
            *event.get('args', ()),
            **kwargs
        )

