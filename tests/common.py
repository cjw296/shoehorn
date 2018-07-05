import sys
from subprocess import check_call
from textwrap import dedent


def run_in_ascii(dir, code, **kw):
    # heavy, but the only way to test that we're handling encoding
    # errors properly
    path = dir.write('test.py', encoding='utf-8', data=dedent(code))
    return check_call([sys.executable, path, dir.getpath('test.log')],
                      env={'LC_ALL': 'C'}, **kw)
