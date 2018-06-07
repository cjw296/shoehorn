from datetime import datetime
from shoehorn.compat import StringIO

import pytest
from testfixtures import compare, TempDirectory, Replace, ShouldRaise

from shoehorn.event import Event
from shoehorn.targets.serialize import JSON, LTSV


@pytest.fixture()
def dir():
    with TempDirectory() as dir:
        yield dir


class TestJSON(object):

    def check_json(self, actual, expected):
        # stdlib includes spaces, rapidjson does not :-/
        if isinstance(actual, bytes):
            actual = actual.replace(b' ', b'')
        else:
            actual = actual.replace(' ', '')
        compare(actual, strict=True, expected=expected)

    def test_simple(self):
        stream = StringIO()
        target = JSON(stream)
        target(Event(x=1))
        self.check_json(stream.getvalue(), expected='{"x":1}')

    def test_date(self):
        stream = StringIO()
        target = JSON(stream)
        target(Event(x=datetime(2016, 3, 11, 5, 45)))
        self.check_json(stream.getvalue(),
                        expected='{"x":"2016-03-1105:45:00"}')

    def test_to_path(self, dir):
        target = JSON(dir.getpath('test.log'))
        target(Event(x=1))
        target.close()
        self.check_json(dir.read('test.log'), expected=b'{"x":1}')

    def test_to_path_append(self, dir):
        path = dir.write('test.log', b'{}\n')
        target = JSON(path)
        target(Event(x=1))
        target.close()
        self.check_json(dir.read('test.log'), expected=b'{}\n{"x":1}')

    def test_to_user_path(self, dir):
        def mock_expanduser(path):
            return path.replace('~', dir.path)
        with Replace('shoehorn.targets.serialize.expanduser', mock_expanduser):
            target = JSON('~/test.log')
        target(Event(x=1))
        target.close()
        self.check_json(dir.read('test.log'), expected=b'{"x":1}')


class TestLTSV(object):

    def test_simple(self, dir):
        with open(dir.getpath('test.log'), 'wb') as stream:
            target = LTSV(stream)
            target(Event((('x', 1), ('y', u'2'), ('z', datetime(2001, 1, 1)))))
        compare(dir.read('test.log', encoding='ascii'),
                expected='x:1\ty:2\tz:2001-01-01 00 00 00\n')

    def test_different_separators(self, dir):
        with open(dir.getpath('test.log'), 'wb') as stream:
            target = LTSV(stream, label_sep='=', item_sep='*')
            target(Event((('x', 1), ('y', u'2'), ('z', datetime(2001, 1, 1)))))
        compare(dir.read('test.log', encoding='ascii'),
                expected='x=1*y=2*z=2001-01-01 00:00:00\n')

    def test_escape_separators(self, dir):
        with open(dir.getpath('test.log'), 'wb') as stream:
            target = LTSV(stream)
            target(Event((('label', ':'), ('item', '\t'), ('line', '\n'))))
        compare(dir.read('test.log', encoding='ascii'),
                expected='label: \titem: \tline: \n')

    def test_bad_encoding(self, dir):
        with open(dir.getpath('test.log'), 'wb') as stream:
            target = LTSV(stream, encoding='ascii')
            target(Event(pound=u"\u00A3"))
        compare(dir.read('test.log', encoding='ascii'),
                expected='pound:?\n')

    def test_path_supplied(self, dir):
        target = LTSV(dir.getpath('test.log'))
        target(Event(pound=u"\u00A3"))
        target.close()
        compare(dir.read('test.log', encoding='utf-8'),
                expected=u'pound:\u00A3\n')
