from unittest import TestCase

from testfixtures import LogCapture, compare

from shoehorn import get_logger
from shoehorn.compat import PY2
from shoehorn.event import Event

logger = get_logger()


class TestStandardLibraryTarget(TestCase):

    def setUp(self):
        self.capture = LogCapture(
            attributes=('name', 'levelname', 'getMessage', 'shoehorn_event')
        )
        self.addCleanup(self.capture.uninstall)

    def test_minimal(self):
        logger.info(event='test')
        self.capture.check(
            ('root', 'INFO', 'None',
             Event(event='test', level='info'))
        )

    def test_named_logger(self):
        logger = get_logger('foo')
        logger.info(event='test')
        self.capture.check(
            ('foo', 'INFO', 'None',
             Event(event='test', logger='foo', level='info'))
        )

    def test_level(self):
        logger.warning(event='test')
        self.capture.check(
            ('root', 'WARNING', 'None',
             Event(event='test', level='warning'))
        )

    def test_sub_args(self):
        logger.info('foo %s', 'bar')
        self.capture.check(
            ('root', 'INFO', 'foo bar',
             Event(message='foo %s', args=('bar', ), level='info'))
        )

    def test_exc_info(self):
        bad = Exception('bad')
        try:
            raise bad
        except:
            logger.exception('foo')
        self.capture.check(
            ('root', 'ERROR', 'foo',
             Event(level='error', message='foo', exc_info=True))
        )
        compare(bad, actual=self.capture.records[-1].exc_info[1])

    def test_stack_info(self):
        if PY2:
            return
        logger.info('foo', stack_info=True)
        self.capture.check(
            ('root', 'INFO', 'foo',
             Event(message='foo', stack_info=True, level='info'))
        )
        compare('Stack (most recent call last):',
                actual=self.capture.records[-1].stack_info.split('\n')[0])

    def test_default_logger(self):
        from shoehorn import logger
        logger.info('er hi')
        self.capture.check(
            ('root', 'INFO', 'er hi',
             Event(message='er hi', level='info'))
        )
