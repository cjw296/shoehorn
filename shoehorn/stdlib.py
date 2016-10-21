from logging import getLogger, INFO, Formatter

sentinel = object()


class StandardLibraryTarget(object):

    def __init__(self, default_level=INFO):
        self.default_level=default_level
        self.loggers = {}
        # do this late in case something adds more levels
        try:
            from logging import _nameToLevel
        except ImportError:
            from logging import _levelNames as _nameToLevel
        self.levels = {n.lower(): l for (n, l) in _nameToLevel.items()
                       if isinstance(n, str)}

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


class ShoehornFormatter(Formatter):

    exclude_keys = {'args', 'exc_info', 'level', 'message', 'stack_info', 'logger'}

    def __init__(self, fmt='%(message)s %(shoehorn_context)s', *args, **kw):
        super(ShoehornFormatter, self).__init__(fmt, *args, **kw)

    def format(self, record):
        post = []
        if getattr(record, 'shoehorn_context', None) is None:
            event = getattr(record, 'shoehorn_event', None)
            if event is None:
                record.shoehorn_context = ''
            else:
                exclude = self.exclude_keys.copy()
                for k, v in sorted(event.items()):
                    if isinstance(v, str) and '\n' in v:
                        post.append('\n'+k+':\n'+v)
                        exclude.add(k)

                record.shoehorn_context = event.serialize(
                    join=' '.join, exclude_keys=exclude
                )
        serialised = super(ShoehornFormatter, self).format(record)
        if record.exc_text is not None:
            serialised, tail = serialised.split('\n', 1)
            post.append('\n'+tail)

        return serialised + ''.join(post)

