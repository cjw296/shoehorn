from datetime import datetime
from io import StringIO
from json import dumps as stdlib_dumps

import pytest
from testfixtures import compare, TempDirectory, Replace, ShouldRaise

from shoehorn.compat import PY2
from shoehorn.event import Event
from shoehorn.targets.serialize import JSON, LTSV, Human, dumps
from .common import run_in_ascii


@pytest.fixture()
def dir():
    with TempDirectory() as dir:
        yield dir


class TestStreams(object):

    def test_stdout_escaping(self, dir):
        with open(dir.getpath('test.out'), 'wb') as target:
            run_in_ascii(dir, stdout=target, code="""
            from shoehorn.targets.serialize import STDOUT
            STDOUT.write(u'pound:\u00A3')
            """)
        compare(dir.read('test.out'), expected=b"pound:\\xa3")

    def test_stderr_escaping(self, dir):
        with open(dir.getpath('test.err'), 'wb') as target:
            run_in_ascii(dir, stderr=target, code="""
            from shoehorn.targets.serialize import STDERR
            STDERR.write(u'pound:\u00A3')
            """)
        compare(dir.read('test.err'), expected=b"pound:\\xa3")


class TestJSON(object):

    def check_json(self, actual, expected):
        if isinstance(actual, bytes):
            actual = actual.decode('utf-8')
        # stdlib includes spaces, rapidjson does not :-/
        actual = actual.replace(' ', '')
        compare(actual, strict=True, expected=expected)

    def test_simple(self):
        stream = StringIO()
        target = JSON(stream)
        target(Event(x=1))
        self.check_json(stream.getvalue(), expected=u'{"x":1}')

    def test_mixed_unicode_byte_values(self):
        stream = StringIO()
        target = JSON(stream)
        target(Event((('bytes', u"\u00A3".encode('latin1')),
                      ('unicodes', u"\u00A3"))))
        if PY2:
            expected = u'{"bytes":"\'\\\\xa3\'","unicodes":"\\u00a3"}'
        elif dumps is stdlib_dumps:
            expected = '{"bytes":"b\'\\\\xa3\'","unicodes":"\\u00a3"}'
        else:
            expected = '{"bytes":"b\'\\\\xa3\'","unicodes":"\\u00A3"}'
        self.check_json(actual=stream.getvalue(), expected=expected)

    def test_floats(self):
        stream = StringIO()
        target = JSON(stream)
        target(Event(nan=float('nan'), p_inf=float('inf'), n_inf=float('-inf')))
        self.check_json(
            stream.getvalue(),
            expected=u'{"nan":NaN,"p_inf":Infinity,"n_inf":-Infinity}'
        )

    def test_date(self):
        stream = StringIO()
        target = JSON(stream)
        target(Event(x=datetime(2016, 3, 11, 5, 45)))
        self.check_json(stream.getvalue(),
                        expected=u'{"x":"2016-03-1105:45:00"}')

    def test_multiline(self):
        stream = StringIO()
        target = JSON(stream)
        target(Event((('windows', '\r\n'), ('linux', '\n'))))
        self.check_json(stream.getvalue(),
                        expected=u'{"windows":"\\r\\n","linux":"\\n"}')

    def test_to_path(self, dir):
        target = JSON(dir.getpath('test.log'))
        target(Event(x=1))
        target.close()
        self.check_json(dir.read('test.log'), expected=u'{"x":1}')

    def test_to_path_append(self, dir):
        path = dir.write('test.log', b'{}\n')
        target = JSON(path)
        target(Event(x=1))
        target.close()
        self.check_json(dir.read('test.log'), expected=u'{}\n{"x":1}')

    def test_to_user_path(self, dir):
        def mock_expanduser(path):
            return path.replace('~', dir.path)
        with Replace('shoehorn.targets.serialize.expanduser', mock_expanduser):
            target = JSON('~/test.log')
        target(Event(x=1))
        target.close()
        self.check_json(dir.read('test.log'), expected=u'{"x":1}')


class TestLTSV(object):

    def test_simple(self):
        stream = StringIO()
        target = LTSV(stream)
        target(Event((('x', 1), ('y', u'2'), ('z', datetime(2001, 1, 1)))))
        compare(stream.getvalue(),
                expected='x:1\ty:2\tz:2001-01-01 00 00 00\n')

    def test_mixed_unicode_byte_values(self):
        stream = StringIO()
        target = LTSV(stream)
        target(Event(byte_pound=u"\u00A3".encode('latin1'),
                     unicode_pound=u"\u00A3"))
        if PY2:
            expected = u"byte_pound:'\\xa3'\tunicode_pound:\xa3\n"
        else:
            expected = "byte_pound:b'\\xa3'\tunicode_pound:\xa3\n"
        compare(expected, actual=stream.getvalue())

    def test_floats(self):
        stream = StringIO()
        target = LTSV(stream)
        target(Event(nan=float('nan'), p_inf=float('inf'), n_inf=float('-inf')))
        compare(stream.getvalue(),
                expected="nan:nan\tp_inf:inf\tn_inf:-inf\n")

    def test_multiline(self):
        stream = StringIO()
        target = LTSV(stream)
        target(Event((('windows', 'foo\r\nbar'), ('linux', 'baz\nbob'))))
        compare(stream.getvalue(),
                expected='windows:foo  bar\tlinux:baz bob\n')

    def test_different_separators(self, dir):
        stream = StringIO()
        target = LTSV(stream, label_sep='=', item_sep='*')
        target(Event((('x', 1), ('y', u'2'), ('z', datetime(2001, 1, 1)))))
        compare(stream.getvalue(),
                expected='x=1*y=2*z=2001-01-01 00:00:00\n')

    def test_escape_separators(self, dir):
        stream = StringIO()
        target = LTSV(stream)
        target(Event((('label', ':'), ('item', '\t'), ('line', '\n'))))
        compare(stream.getvalue(),
                expected='label: \titem: \tline: \n')

    def test_bad_encoding(self, dir):
        run_in_ascii(dir, """
        from shoehorn.event import Event
        from shoehorn.targets.serialize import LTSV
        import sys
        target = LTSV(sys.argv[1])
        target(Event(pound=u"\u00A3"))
        """)
        compare(dir.read('test.log'), expected=b"pound:\\xa3\n")

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
            LTSV(StringIO(), **{sep: 'xx'})

    @pytest.mark.parametrize("sep", ['label_sep', 'item_sep'])
    def test_separator_too_long(self, sep):
        with ShouldRaise(AssertionError(
            "space cannot be used as a separator"
        )):
            LTSV(StringIO(), **{sep: ' '})


class TestHuman(object):

    def test_simple(self, dir):
        stream = StringIO()
        target = Human(stream)
        target(Event((('x', 1), ('y', '2'), ('z', datetime(2001, 1, 1)))))
        compare(stream.getvalue(),
                expected="x=1, y='2', z=datetime.datetime(2001, 1, 1, 0, 0)\n")

    def test_mixed_unicode_byte_values(self):
        stream = StringIO()
        target = Human(stream)
        target(Event(byte_pound=u"\u00A3".encode('latin1'),
                     unicode_pound=u"\u00A3"))
        if PY2:
            expected = "byte_pound='\\xa3', unicode_pound=u'\\xa3'\n"
        else:
            expected = "byte_pound=b'\\xa3', unicode_pound='\xa3'\n"
        compare(expected, actual=stream.getvalue())

    def test_floats(self):
        stream = StringIO()
        target = Human(stream)
        target(Event(nan=float('nan'), p_inf=float('inf'), n_inf=float('-inf')))
        compare(stream.getvalue(),
                expected='nan=nan, p_inf=inf, n_inf=-inf\n')

    def test_prefix(self):
        stream = StringIO()
        target = Human(stream, prefix='{z:%Y-%m} {x!r} {a}: ')
        target(Event((
            ('x', 1),
            ('y', '2'),
            ('z', datetime(2001, 1, 1)),
            ('a', 'foo'),
            ('b', 'bar'),
        )))
        compare(stream.getvalue(),
                expected="2001-01 1 foo: y='2', b='bar'\n")

    def test_ignore(self):
        stream = StringIO()
        target = Human(stream, ignore={'z'})
        target(Event((('x', 1), ('y', '2'), ('z', datetime(2001, 1, 1)))))
        compare(stream.getvalue(),
                expected="x=1, y='2'\n")

    def test_only(self):
        stream = StringIO()
        target = Human(stream, only={'x', 'y'})
        target(Event((('x', 1), ('y', '2'), ('z', datetime(2001, 1, 1)))))
        compare(stream.getvalue(),
                expected="x=1, y='2'\n")

    def test_bad_encoding(self, dir):
        run_in_ascii(dir, """
        from shoehorn.event import Event
        from shoehorn.targets.serialize import Human
        import sys
        target = Human(sys.argv[1])
        target(Event(pound=u"\u00A3"))
        """)
        if PY2:
            expected = b"pound=u'\\xa3'\n"
        else:
            expected = b"pound='\\xa3'\n"
        compare(expected, actual=dir.read('test.log'))

    @pytest.mark.parametrize("prefix", ['{}', '{0}', '{!}', '{:.foo}'])
    def test_bad_prefixes(self, prefix):
        with ShouldRaise(AssertionError("bad prefix templating: "+prefix)):
            Human(StringIO(), prefix=prefix)

    def test_newlines_values(self):
        stream = StringIO()
        target = Human(stream)
        target(Event((('x', 1), ('c', 'foo\nbar\n'),
                      ('y', '2'), ('b', 'baz\r\nbob'))))
        compare(stream.getvalue(),
                expected="x=1, y='2'\n"
                         "c:\n"
                         "foo\n"
                         "bar\n"
                         "\n"
                         "b:\n"
                         "baz\r\n"
                         "bob\n")

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
