from collections import OrderedDict

from .event import Event


class Logger(object):

    def __init__(self, target):
        self.target = target
        self.context = OrderedDict()

    # context methods

    def bind(self, **context):
        return self.bind_ordered(*context.items())

    def bind_ordered(self, *context):
        """
        :param context:
          A sequence of ``(name, value)`` tuples providing context to bind
          to this logger. The order of these tuples will be preserved.
        """
        logger = self.__class__(self.target)
        logger.context.update(self.context)
        logger.context.update(context)
        return logger

    def alter(self, **context):
        self.context.update(context)

    # logging methods

    def _log(self, level, args, context):
        event = Event(self.context)
        event.update(context)
        event['level'] = level
        if args:
            event['message'] = args[0]
            args = args[1:]
            if args:
                event['args'] = args
        self.target(event)

    def debug(self, *args, **context):
        self._log('debug', args, context)

    def info(self, *args, **context):
        self._log('info', args, context)

    def warning(self, *args, **context):
        self._log('warning', args, context)

    warn = warning

    def error(self, *args, **context):
        self._log('error', args, context)

    def exception(self, *args, **context):
        context['exc_info'] = True
        self._log('error', args, context)

    def critical(self, *args, **context):
        self._log('critical', args, context)

    fatal = critical

    def log(self, level, *args, **context):
        self._log(level, args, context)

    def log_ordered(self, level, *context):
        """
        :param level:
          A string giving the level at which this :class:`Event` should be
          logged.
        :param context:
          A sequence of ``(name, value)`` tuples providing the context to log.
          The order of these tuples will be preserved.
        """
        self._log(level, (), OrderedDict(context))
