from datetime import datetime
from shoehorn.compat import StringIO

import pytest
from testfixtures import compare, TempDirectory, Replace

from shoehorn.event import Event
from shoehorn.targets.serialize import JSON


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
