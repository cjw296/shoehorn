from collections import OrderedDict
from logging import WARNING, StreamHandler, getLogger, FileHandler
from tempfile import NamedTemporaryFile

from testfixtures import LogCapture, OutputCapture, compare
import pytest

from shoehorn import get_logger
from shoehorn.compat import PY2, PY36
from shoehorn.event import Event
from shoehorn.stdlib import StandardLibraryTarget, ShoehornFormatter


@pytest.fixture(autouse=True)
def capture():
    # also sets level and makes sure we leave no handlers around:
    with LogCapture(
        attributes=('name', 'levelname', 'getMessage', 'shoehorn_event')
    ) as log:
        yield log


class TestStandardLibraryTarget(object):


    @pytest.fixture()
    def target(self):
        return StandardLibraryTarget()

    def test_minimal(self, target, capture):
        event = Event(event='test')
        target(event)
        capture.check(
            ('root', 'INFO', '', event)
        )

    def test_specifify_default_level(self, capture):
        target = StandardLibraryTarget(default_level=WARNING)
        event = Event(event='test')
        target(event)
        capture.check(
            ('root', 'WARNING', '', event)
        )

    def test_named_logger(self, target, capture):
        event = Event(event='test', logger='foo')
        target(event)
        capture.check(
            ('foo', 'INFO', '', event)
        )

    def test_numeric_level(self, target, capture):
        event = Event(event='test', level=WARNING)
        target(event)
        capture.check(
            ('root', 'WARNING', '', event)
        )

    def test_string_level(self, target, capture):
        event = Event(event='test', level='warning')
        target(event)
        capture.check(
            ('root', 'WARNING', '', event)
        )

    def test_unknown_string_level(self, target, capture):
        event = Event(event='test', level='yuhwut?')
        target(event)
        capture.check(
            ('root', 'INFO', '', event)
        )

    def test_sub_args(self, target, capture):
        event = Event(message='foo %s', args=('bar', ))
        target(event)
        capture.check(
            ('root', 'INFO', 'foo bar', event)
        )

    def test_exc_info(self, target, capture):
        bad = Exception('bad')
        try:
            raise bad
        except:
            event = Event(level='error', message='foo', exc_info=True)
            target(event)
        capture.check(
            ('root', 'ERROR', 'foo', event)
        )
        compare(bad, actual=capture.records[-1].exc_info[1])

    def test_stack_info(self, target, capture):
        if PY2:
            return
        event = Event(message='foo', stack_info=True)
        target(event)
        capture.check(
            ('root', 'INFO', 'foo', event)
        )
        compare('Stack (most recent call last):',
                actual=capture.records[-1].stack_info.split('\n')[0])


class TestShoehornFormatter(object):

    @pytest.fixture()
    def output(self):
        return OutputCapture()


    @pytest.fixture()
    def handler(self, output):
        with output:
            handler = StreamHandler()
            handler.setFormatter(ShoehornFormatter())
        return handler

    @pytest.fixture(autouse=True)
    def logger(self, handler):
        logger = getLogger()
        logger.addHandler(handler)
        return logger

    def test_no_context(self, logger, output):
        kw = dict(exc_info=True)
        if not PY2:
            kw['stack_info']=True
        try:
            1/0
        except:
            logger.info('foo %s', 'bar', **kw)
        compare(output.captured.splitlines()[0],
                expected='foo bar')

    def test_extra_context(self, output, logger):
        kw = OrderedDict([('exc_info', True),
                          ('context', 'oh hai'),
                          ('other', 1)])
        if not PY2:
            kw['stack_info']=True
        try:
            1/0
        except:
            logger = get_logger()
            if PY36:
                logger.info('foo %s', 'bar', **kw)
            else:
                logger.log_ordered('info',
                                   ('message', 'foo bar'), *kw.items())

        compare(output.captured.splitlines()[0],
                expected="foo bar context='oh hai' other=1")

    def test_bound_logger(self, handler, output):
        handler.setFormatter(ShoehornFormatter(
            '%(name)s %(message)s%(shoehorn_context)s'
        ))
        get_logger('foo.bar').info('oh hai')
        compare(output.captured,
                expected="foo.bar oh hai\n")

    def test_multiline_value_string(self, output):
        try:
            1/0
        except:
            get_logger().exception('bad', diff='foo\nbar')

        compare(output.captured.splitlines()[:5],
                expected=[
                    'bad',
                    'diff:',
                    'foo',
                    'bar',
                    'Traceback (most recent call last):',
                ])

    def test_multiline_message_interpolation(self, output):
        log = get_logger().bind(k='v')
        log.info('oh\n%s\nryl', 'ffs')
        compare(output.captured,
                expected="oh\nffs\nryl k='v'\n")

    def test_multiline_value_unicode_to_file(self, logger):
        disk_file = NamedTemporaryFile(mode='ab+')
        handler = FileHandler(disk_file.name)
        handler.setFormatter(ShoehornFormatter())
        logger.addHandler(handler)
        try:
            1/0
        except:
            get_logger().exception('bad', short='x', diff=u'foo\n\U0001F4A9')

        disk_file.seek(0)
        compare(disk_file.readlines()[:5],
                expected=[
                    b"bad short='x'\n",
                    b'diff:\n',
                    b'foo\n',
                    b'\xf0\x9f\x92\xa9\n',
                    b'Traceback (most recent call last):\n',
                ])

    if not PY2:
        def test_multiline_value_bytes(self, output):
            try:
                1/0
            except:
                get_logger().exception('bad', diff=b'foo\nbar')

            compare(output.captured.splitlines()[:2],
                    expected=[
                        "bad diff=b'foo\\nbar'",
                        'Traceback (most recent call last):',
                    ])

    def test_no_message(self, output):
        get_logger().info(bar='foo')
        compare(output.captured.splitlines()[0],
                expected=" bar='foo'")

    def test_unbound(self, output):
        get_logger().info('the message')
        compare(output.captured.splitlines(),
                expected=["the message"])
