from testfixtures import compare

from shoehorn import Stack
from shoehorn.targets.filter import RemoveKeys, RemoveKeysByPattern
from shoehorn.testing import TestTarget


def test_remove_keys():
        t = TestTarget()
        s = Stack(
            RemoveKeys('foo', 'bar'),
            t
        )
        s({'foo': 'bar', 'bar': 'baz', 'bob': 1})
        s({'bob': 2})
        compare(t.events, expected=[{'bob': 1}, {'bob': 2}])


def test_remove_keys_pattern():
        t = TestTarget()
        s = Stack(
            RemoveKeysByPattern('bad_'),
            t
        )
        s({'bad_foo': 'bar', 'bad_bar': 'baz', 'bob': 1})
        s({'bob': 2})
        compare(t.events, expected=[{'bob': 1}, {'bob': 2}])
