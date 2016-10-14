from unittest import TestCase

from testfixtures import compare, ShouldRaise

from shoehorn import Logger
from shoehorn.event import Event


class TestLogger(TestCase):

    def setUp(self):
        self.records = []
        self.logger = Logger(self.records.append)

    def check(self, *expected):
        compare(expected, actual=self.records)

    def test_minimal(self):
        self.logger.debug(event='foo')
        self.logger.info(event='foo')
        self.logger.warning(event='foo')
        self.logger.warn(event='foo')
        self.logger.error(event='foo')
        self.logger.exception(event='foo')
        self.logger.critical(event='foo')
        self.logger.fatal(event='foo')
        self.logger.log(level=42, event='foo')
        self.check(
            Event(level='debug', event='foo'),
            Event(level='info', event='foo'),
            Event(level='warning', event='foo'),
            Event(level='warning', event='foo'),
            Event(level='error', event='foo'),
            Event(level='error', event='foo', exc_info=True),
            Event(level='critical', event='foo'),
            Event(level='critical', event='foo'),
            Event(level=42, event='foo'),
        )


    def test_stdlib(self):
        self.logger.debug('foo %s', 'bar',
                          exc_info=None, extra=None, stack_info=False)
        self.logger.info('foo %s', 'bar',
                         exc_info=None, extra=None, stack_info=False)
        self.logger.warning('foo %s', 'bar',
                            exc_info=None, extra=None, stack_info=False)
        self.logger.warn('foo %s', 'bar',
                         exc_info=None, extra=None, stack_info=False)
        self.logger.error('foo %s', 'bar',
                          exc_info=None, extra=None, stack_info=False)
        self.logger.exception('foo %s', 'bar',
                              exc_info=None, extra=None, stack_info=False)
        self.logger.critical('foo %s', 'bar',
                             exc_info=None, extra=None, stack_info=False)
        self.logger.fatal('foo %s', 'bar',
                          exc_info=None, extra=None, stack_info=False)
        self.logger.log(42, 'foo %s', 'bar',
                        exc_info=None, extra=None, stack_info=False)
        self.check(
            Event(level='debug', message='foo %s', args=('bar', ),
                  exc_info=None, extra=None, stack_info=False),
            Event(level='info', message='foo %s', args=('bar', ),
                  exc_info=None, extra=None, stack_info=False),
            Event(level='warning', message='foo %s', args=('bar', ),
                  exc_info=None, extra=None, stack_info=False),
            Event(level='warning', message='foo %s', args=('bar', ),
                  exc_info=None, extra=None, stack_info=False),
            Event(level='error', message='foo %s', args=('bar', ),
                  exc_info=None, extra=None, stack_info=False),
            Event(level='error', message='foo %s', args=('bar', ),
                  exc_info=True, extra=None, stack_info=False),
            Event(level='critical', message='foo %s', args=('bar', ),
                  exc_info=None, extra=None, stack_info=False),
            Event(level='critical', message='foo %s', args=('bar', ),
                  exc_info=None, extra=None, stack_info=False),
            Event(level=42, message='foo %s', args=('bar', ),
                  exc_info=None, extra=None, stack_info=False),
        )

    def test_simple(self):
        self.logger.debug('foo')
        self.logger.info('foo')
        self.logger.warning('foo')
        self.logger.warn('foo')
        self.logger.error('foo')
        self.logger.exception('foo')
        self.logger.critical('foo')
        self.logger.fatal('foo')
        self.check(
            Event(level='debug', message='foo'),
            Event(level='info', message='foo'),
            Event(level='warning', message='foo'),
            Event(level='warning', message='foo'),
            Event(level='error', message='foo'),
            Event(level='error', message='foo', exc_info=True),
            Event(level='critical', message='foo'),
            Event(level='critical', message='foo'),
        )

    def test_includes_magic_vars(self):
        # built-in wins!
        self.logger.debug('foo', 'bar', 'baz', message='bob', args='er?')
        with ShouldRaise(TypeError):
            self.logger.log(42, 'foo', 'bar', 'baz',
                            message='bob', args='er?', level=50)
        self.check(
            Event(level='debug', message='foo', args=('bar', 'baz')),
        )

    def test_bind(self):
        logger = self.logger.bind(name='my.logger')
        logger.debug('foo')
        self.logger.debug('bar')
        self.check(
            Event(name='my.logger', level='debug', message='foo'),
            Event(level='debug', message='bar'),
        )

    def test_nested_bind(self):
        log = self.logger.bind(keep=1, replace=2)
        log.info(event='first bind')
        log = log.bind(replace=3, new=4)
        log.info(event='second bind')
        self.check(
            Event(level='info', event='first bind', keep=1, replace=2),
            Event(level='info', event='second bind', keep=1, replace=3, new=4),
        )

    def test_alter(self):
        self.logger.info('foo')
        self.logger.alter(name='my.logger')
        self.logger.info('bar')
        self.check(
            Event(level='info', message='foo'),
            Event(name='my.logger', level='info', message='bar'),
        )
