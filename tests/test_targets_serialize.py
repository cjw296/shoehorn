from datetime import datetime
from io import BytesIO
from json import dumps as stdlib_dumps

import pytest
from testfixtures import compare, TempDirectory, Replace, ShouldRaise

from shoehorn.compat import PY2
from shoehorn.event import Event
from shoehorn.targets.serialize import JSON, LTSV, Human, dumps


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

    def test_mixed_unicode_byte_values(self):
        stream = BytesIO()
        target = JSON(stream)
        target(Event((('bytes', u"\u00A3".encode('latin1')),
                      ('unicodes', u"\u00A3"))))
        if PY2:
            expected = '{"bytes":"\'\\\\xa3\'","unicodes":"\\u00a3"}'
        elif dumps is stdlib_dumps:
            expected = b'{"bytes":"b\'\\\\xa3\'","unicodes":"\\u00a3"}'
        else:
            expected = b'{"bytes":"b\'\\\\xa3\'","unicodes":"\\u00A3"}'
        self.check_json(actual=stream.getvalue(), expected=expected)

    def test_floats(self):
        stream = BytesIO()
        target = JSON(stream)
        target(Event(nan=float('nan'), p_inf=float('inf'), n_inf=float('-inf')))
        self.check_json(
            stream.getvalue(),
            expected=b'{"nan":NaN,"p_inf":Infinity,"n_inf":-Infinity}'
        )

    def test_date(self):
        stream = BytesIO()
        target = JSON(stream)
        target(Event(x=datetime(2016, 3, 11, 5, 45)))
        self.check_json(stream.getvalue(),
                        expected=b'{"x":"2016-03-1105:45:00"}')

    def test_multiline(self):
        stream = BytesIO()
        target = JSON(stream)
        target(Event((('windows', '\r\n'), ('linux', '\n'))))
        self.check_json(stream.getvalue(),
                        expected=b'{"windows":"\\r\\n","linux":"\\n"}')

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

    def test_mixed_unicode_byte_values(self):
        stream = BytesIO()
        target = LTSV(stream)
        target(Event(byte_pound=u"\u00A3".encode('latin1'),
                     unicode_pound=u"\u00A3"))
        if PY2:
            expected = b"byte_pound:'\\xa3'\tunicode_pound:\xc2\xa3\n"
        else:
            expected=b"byte_pound:b'\\xa3'\tunicode_pound:\xc2\xa3\n"
        compare(expected, actual=stream.getvalue())

    def test_floats(self):
        stream = BytesIO()
        target = LTSV(stream)
        target(Event(nan=float('nan'), p_inf=float('inf'), n_inf=float('-inf')))
        compare(stream.getvalue(),
                expected=b"nan:nan\tp_inf:inf\tn_inf:-inf\n")

    def test_multiline(self):
        stream = BytesIO()
        target = LTSV(stream)
        target(Event((('windows', 'foo\r\nbar'), ('linux', 'baz\nbob'))))
        compare(stream.getvalue(),
                expected=b'windows:foo  bar\tlinux:baz bob\n')

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

    def test_to_path_append(self, dir):
        path = dir.write('test.log', b'{}\n')
        target = LTSV(path)
        target(Event(x=1))
        target.close()
        compare(dir.read('test.log', encoding='utf-8'),
                expected=u'{}\nx:1\n')

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

    def test_mixed_unicode_byte_values(self):
        stream = BytesIO()
        target = Human(stream)
        target(Event(byte_pound=u"\u00A3".encode('latin1'),
                     unicode_pound=u"\u00A3"))
        if PY2:
            expected = "byte_pound='\\xa3', unicode_pound=u'\\xa3'\n"
        else:
            expected = b"byte_pound=b'\\xa3', unicode_pound='\xc2\xa3'\n"
        compare(expected, actual=stream.getvalue())

    def test_floats(self):
        stream = BytesIO()
        target = Human(stream)
        target(Event(nan=float('nan'), p_inf=float('inf'), n_inf=float('-inf')))
        compare(stream.getvalue(),
                expected=b'nan=nan, p_inf=inf, n_inf=-inf\n')

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
    def test_bad_prefixes(self, prefix):
        with ShouldRaise(AssertionError("bad prefix templating: "+prefix)):
            Human(BytesIO(), prefix=prefix)

    def test_newlines_values(self):
        stream = BytesIO()
        target = Human(stream)
        target(Event((('x', 1), ('c', 'foo\nbar\n'),
                      ('y', '2'), ('b', 'baz\r\nbob'))))
        compare(stream.getvalue(),
                expected=b"x=1, y='2'\n"
                         b"c:\n"
                         b"foo\n"
                         b"bar\n"
                         b"\n"
                         b"b:\n"
                         b"baz\r\n"
                         b"bob\n")

    def test_path_supplied(self, dir):
        target = Human(dir.getpath('test.log'))
        target(Event(pound=u"\u00A3"))
        target.close()
        if PY2:
            expected=u"pound=u'\\xa3'\n"
        else:
            expected=u"pound='\u00A3'\n"
        compare(expected, actual=dir.read('test.log', encoding='utf-8'))

    def test_to_path_append(self, dir):
        path = dir.write('test.log', b'{}\n')
        target = Human(path)
        target(Event(x=1))
        target.close()
        compare(dir.read('test.log', encoding='utf-8'),
                expected='{}\nx=1\n')
