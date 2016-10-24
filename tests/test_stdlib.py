from logging import WARNING, StreamHandler, getLogger, FileHandler
from tempfile import NamedTemporaryFile
from unittest import TestCase

from testfixtures import LogCapture, OutputCapture, compare

from shoehorn import get_logger
from shoehorn.compat import PY2
from shoehorn.event import Event
from shoehorn.stdlib import StandardLibraryTarget, ShoehornFormatter



class TestStandardLibraryTarget(TestCase):

    def setUp(self):
        self.capture = LogCapture(
            attributes=('name', 'levelname', 'getMessage', 'shoehorn_event')
        )
        self.addCleanup(self.capture.uninstall)
        self.target = StandardLibraryTarget()

    def test_minimal(self):
        event = Event(event='test')
        self.target(event)
        self.capture.check(
            ('root', 'INFO', 'None', event)
        )

    def test_specifify_default_level(self):
        target = StandardLibraryTarget(default_level=WARNING)
        event = Event(event='test')
        target(event)
        self.capture.check(
            ('root', 'WARNING', 'None', event)
        )

    def test_named_logger(self):
        event = Event(event='test', logger='foo')
        self.target(event)
        self.capture.check(
            ('foo', 'INFO', 'None', event)
        )

    def test_numeric_level(self):
        event = Event(event='test', level=WARNING)
        self.target(event)
        self.capture.check(
            ('root', 'WARNING', 'None', event)
        )

    def test_string_level(self):
        event = Event(event='test', level='warning')
        self.target(event)
        self.capture.check(
            ('root', 'WARNING', 'None', event)
        )

    def test_unknown_string_level(self):
        event = Event(event='test', level='yuhwut?')
        self.target(event)
        self.capture.check(
            ('root', 'INFO', 'None', event)
        )

    def test_sub_args(self):
        event = Event(message='foo %s', args=('bar', ))
        self.target(event)
        self.capture.check(
            ('root', 'INFO', 'foo bar', event)
        )

    def test_exc_info(self):
        bad = Exception('bad')
        try:
            raise bad
        except:
            event = Event(level='error', message='foo', exc_info=True)
            self.target(event)
        self.capture.check(
            ('root', 'ERROR', 'foo', event)
        )
        compare(bad, actual=self.capture.records[-1].exc_info[1])

    def test_stack_info(self):
        if PY2:
            return
        event = Event(message='foo', stack_info=True)
        self.target(event)
        self.capture.check(
            ('root', 'INFO', 'foo', event)
        )
        compare('Stack (most recent call last):',
                actual=self.capture.records[-1].stack_info.split('\n')[0])


class TestShoehornFormatter(TestCase):

    def setUp(self):
        # so we don't leave a mess
        self.capture = LogCapture()
        self.addCleanup(self.capture.uninstall)
        with OutputCapture() as output:
            self.handler = StreamHandler()
        self.output = output
        self.handler.setFormatter(ShoehornFormatter())
        self.logger = getLogger()
        self.logger.addHandler(self.handler)

    def test_no_context(self):
        kw = dict(exc_info=True)
        if not PY2:
            kw['stack_info']=True
        try:
            1/0
        except:
            self.logger.info('foo %s', 'bar', **kw)
        compare(self.output.captured.splitlines()[0],
                expected='foo bar ')

    def test_extra_context(self):
        kw = dict(exc_info=True, context='oh hai', other=1)
        if not PY2:
            kw['stack_info']=True
        try:
            1/0
        except:
            get_logger().info('foo %s', 'bar', **kw)
        compare(self.output.captured.splitlines()[0],
                expected="foo bar context='oh hai' other=1")

    def test_bound_logger(self):
        self.handler.setFormatter(ShoehornFormatter(
            '%(name)s %(message)s%(shoehorn_context)s'
        ))
        get_logger('foo.bar').info('oh hai')
        compare(self.output.captured,
                expected="foo.bar oh hai\n")

    def test_multiline_value_string(self):
        try:
            1/0
        except:
            get_logger().exception('bad', diff='foo\nbar')

        compare(self.output.captured.splitlines()[:5],
                expected=[
                    'bad ',
                    'diff:',
                    'foo',
                    'bar',
                    'Traceback (most recent call last):',
                ])

    def test_multiline_value_unicode_to_file(self):
        disk_file = NamedTemporaryFile(mode='ab+')
        handler = FileHandler(disk_file.name)
        handler.setFormatter(ShoehornFormatter())
        self.logger.addHandler(handler)
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
        def test_multiline_value_bytes(self):
            try:
                1/0
            except:
                get_logger().exception('bad', diff=b'foo\nbar')

            compare(self.output.captured.splitlines()[:2],
                    expected=[
                        "bad diff=b'foo\\nbar'",
                        'Traceback (most recent call last):',
                    ])
