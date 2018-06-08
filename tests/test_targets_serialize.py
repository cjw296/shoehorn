from datetime import datetime
from io import BytesIO

import pytest
from testfixtures import compare, TempDirectory, Replace, ShouldRaise

from shoehorn.compat import PY2
from shoehorn.event import Event
from shoehorn.targets.serialize import JSON, LTSV, Human


@pytest.fixture()
def dir():
    with TempDirectory() as dir:
        yield dir


class TestJSON(object):

    def check_json(self, actual, expected):
        # stdlib includes spaces, rapidjson does not :-/
        actual = actual.replace(b' ', b'')
        compare(actual, strict=True, expected=expected)

    def test_simple(self):
        stream = BytesIO()
        target = JSON(stream)
        target(Event(x=1))
        self.check_json(stream.getvalue(), expected=b'{"x":1}')

    def test_date(self):
        stream = BytesIO()
        target = JSON(stream)
        target(Event(x=datetime(2016, 3, 11, 5, 45)))
        self.check_json(stream.getvalue(),
                        expected=b'{"x":"2016-03-1105:45:00"}')

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
        stream = BytesIO()
        target = LTSV(stream)
        target(Event((('x', 1), ('y', u'2'), ('z', datetime(2001, 1, 1)))))
        compare(stream.getvalue(),
                expected=b'x:1\ty:2\tz:2001-01-01 00 00 00\n')

    def test_different_separators(self, dir):
        stream = BytesIO()
        target = LTSV(stream, label_sep='=', item_sep='*')
        target(Event((('x', 1), ('y', u'2'), ('z', datetime(2001, 1, 1)))))
        compare(stream.getvalue(),
                expected=b'x=1*y=2*z=2001-01-01 00:00:00\n')

    def test_escape_separators(self, dir):
        stream = BytesIO()
        target = LTSV(stream)
        target(Event((('label', ':'), ('item', '\t'), ('line', '\n'))))
        compare(stream.getvalue(),
                expected=b'label: \titem: \tline: \n')

    def test_bad_encoding(self, dir):
        stream = BytesIO()
        target = LTSV(stream, encoding='ascii')
        target(Event(pound=u"\u00A3"))
        compare(stream.getvalue(),
                expected=b'pound:?\n')

    def test_path_supplied(self, dir):
        target = LTSV(dir.getpath('test.log'))
        target(Event(pound=u"\u00A3"))
        target.close()
        compare(dir.read('test.log', encoding='utf-8'),
                expected=u'pound:\u00A3\n')

    @pytest.mark.parametrize("sep", ['label_sep', 'item_sep'])
    def test_separator_too_long(self, sep):
        with ShouldRaise(AssertionError(
            "separators can only be one character is length"
        )):
            LTSV(BytesIO(), **{sep: 'xx'})

    @pytest.mark.parametrize("sep", ['label_sep', 'item_sep'])
    def test_separator_too_long(self, sep):
        with ShouldRaise(AssertionError(
            "space cannot be used as a separator"
        )):
            LTSV(BytesIO(), **{sep: ' '})


class TestHuman(object):

    def test_simple(self, dir):
        stream = BytesIO()
        target = Human(stream)
        target(Event((('x', 1), ('y', '2'), ('z', datetime(2001, 1, 1)))))
        compare(stream.getvalue(),
                expected=b"x=1, y='2', z=datetime.datetime(2001, 1, 1, 0, 0)\n")

    def test_prefix(self, dir):
        stream = BytesIO()
        target = Human(stream, prefix='{z:%Y-%m} {x!r} {a}: ')
        target(Event((
            ('x', 1),
            ('y', '2'),
            ('z', datetime(2001, 1, 1)),
            ('a', 'foo'),
            ('b', 'bar'),
        )))
        compare(stream.getvalue(),
                expected=b"2001-01 1 foo: y='2', b='bar'\n")

    def test_ignore(self, dir):
        stream = BytesIO()
        target = Human(stream, ignore={'z'})
        target(Event((('x', 1), ('y', '2'), ('z', datetime(2001, 1, 1)))))
        compare(stream.getvalue(),
                expected=b"x=1, y='2'\n")

    def test_only(self, dir):
        stream = BytesIO()
        target = Human(stream, only={'x', 'y'})
        target(Event((('x', 1), ('y', '2'), ('z', datetime(2001, 1, 1)))))
        compare(stream.getvalue(),
                expected=b"x=1, y='2'\n")

    def test_bad_encoding(self, dir):
        stream = BytesIO()
        target = Human(stream, encoding='ascii')
        target(Event(pound=u"\u00A3"))
        if PY2:
            expected="pound=u'\\xa3'\n"
        else:
            expected=b"pound='?'\n"
        compare(expected, actual=stream.getvalue())

    @pytest.mark.parametrize("prefix", ['{}', '{0}', '{!}', '{:.foo}'])
    def test_empty_curlies(self, prefix):
        with ShouldRaise(AssertionError("bad prefix templating: "+prefix)):
            Human(BytesIO(), prefix=prefix)
