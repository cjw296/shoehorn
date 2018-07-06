import sys

from testfixtures import compare

from .common import run_in_ascii


def test_error_handling(dir):
    with open(dir.getpath('test.out'), 'wb') as out,\
         open(dir.getpath('test.err'), 'wb') as err:
        run_in_ascii(dir, stdout=out, stderr=err, code="""
        from shoehorn import logging, logger
        def go_boom(event):
            raise Exception('boom!')
        logging.push(go_boom)
        logger.info('hai!')
        print('all good!')
        """)
    compare(dir.read('test.out'), expected=b"all good!\n")
    err = dir.read('test.err', encoding=sys.getdefaultencoding())
    assert err.startswith(
        "event=\"Event(level='info', message='hai!')\"\n"
        "traceback:\n"
        "Traceback (most recent call last):"), err
    assert err.endswith("\nException: boom!\n"), err


def test_error_handling_for_encoding_problem(dir):
    with open(dir.getpath('test.out'), 'wb') as out,\
         open(dir.getpath('test.err'), 'wb') as err:
        run_in_ascii(dir, stdout=out, stderr=err, code="""
        from shoehorn import logging, logger
        def go_boom(event):
            raise Exception(u'\u00A3')
        logging.push(go_boom)
        logger.info('hai!')
        print('all good!')
        """)
    compare(dir.read('test.out'), expected=b"all good!\n")
    err = dir.read('test.err', encoding=sys.getdefaultencoding())
    assert err.startswith(
        "event=\"Event(level='info', message='hai!')\"\n"
        "traceback:\n"
        "Traceback (most recent call last):"), err
    assert err.endswith("\nException: \\xa3\n"), err
