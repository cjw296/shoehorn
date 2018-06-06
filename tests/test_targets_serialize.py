from io import StringIO

import pytest
from testfixtures import compare, TempDirectory, Replace

from shoehorn.event import Event
from shoehorn.targets.serialize import JSON


@pytest.fixture()
def dir():
    with TempDirectory() as dir:
        yield dir


class TestJson(object):

    def test_simple(self):
        stream = StringIO()
        target = JSON(stream)
        target(Event(x=1))
        compare(stream.getvalue(), strict=True, expected='{"x":1}')

    def test_to_path(self, dir):
        target = JSON(dir.getpath('test.log'))
        target(Event(x=1))
        target.close()
        compare(dir.read('test.log'), strict=True, expected=b'{"x":1}')

    def test_to_path_append(self, dir):
        path = dir.write('test.log', b'{}\n')
        target = JSON(path)
        target(Event(x=1))
        target.close()
        compare(dir.read('test.log'), strict=True, expected=b'{}\n{"x":1}')

    def test_to_user_path(self, dir):
        def mock_expanduser(path):
            return path.replace('~', dir.path)
        with Replace('shoehorn.targets.serialize.expanduser', mock_expanduser):
            target = JSON('~/test.log')
        target(Event(x=1))
        target.close()
        compare(dir.read('test.log'), strict=True, expected=b'{"x":1}')
