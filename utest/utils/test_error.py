import unittest
import sys
import re

from robot.utils.asserts import assert_equals, assert_true, assert_raises
from robot import utils
if utils.is_jython:
    import JavaExceptions
    java_exceptions = JavaExceptions()

from robot.utils.error import get_error_details, get_error_message, PythonErrorDetails


class TestGetErrorDetails(unittest.TestCase):

    def test_get_error_details_python(self):
        for exception, msg, exp_msg in [
                    (AssertionError, 'My Error', 'My Error'),
                    (AssertionError, None, 'AssertionError'),
                    (Exception, 'Another Error', 'Another Error'),
                    (Exception, None, 'Exception'),
                    (ValueError, 'Something', 'ValueError: Something'),
                    (ValueError, None, 'ValueError'),
                    (AssertionError, 'Msg\nin 3\nlines', 'Msg\nin 3\nlines'),
                    (ValueError, '2\nlines', 'ValueError: 2\nlines')]:
            try:
                raise exception, msg
            except:
                message, details = get_error_details()
                assert_equals(message, get_error_message())
            assert_equals(message, exp_msg)
            assert_true(details.startswith('Traceback'))
            assert_true(exp_msg not in details)

    if utils.is_jython:

        def test_get_error_details_java(self):
            for exception, msg, expected in [
                    ('AssertionError', 'My Error', 'My Error'),
                    ('AssertionError', None, 'AssertionError'),
                    ('RuntimeException', 'Another Error', 'Another Error'),
                    ('RuntimeException', None, 'RuntimeException'),
                    ('ArithmeticException', 'foo', 'ArithmeticException: foo'),
                    ('ArithmeticException', None, 'ArithmeticException'),
                    ('AssertionError', 'Msg\nin 3\nlines', 'Msg\nin 3\nlines'),
                    ('IOException', '1\n2', 'IOException: 1\n2'),
                    ('RuntimeException', 'embedded', 'embedded'),
                    ('IOException', 'IOException: emb', 'IOException: emb')]:
                try:
                    throw_method = getattr(java_exceptions, 'throw'+exception)
                    throw_method(msg)
                except:
                    message, details = get_error_details()
                    assert_equals(message, get_error_message())
                assert_equals(message, expected)
                lines = details.splitlines()
                assert_true(exception in lines[0])
                for line in lines[1:]:
                    line.strip().startswith('at ')

        def test_message_removed_from_details_java(self):
            for msg in ['My message', 'My\nmultiline\nmessage']:
                try:
                    java_exceptions.throwRuntimeException(msg)
                except:
                    message, details = get_error_details()
                assert_true(message not in details)
                line1, line2 = details.splitlines()[0:2]
                assert_equals('java.lang.RuntimeException: ', line1)
                assert_true(line2.strip().startswith('at '))


class TestRemoveRobotEntriesFromTraceback(unittest.TestCase):

    def test_both_robot_and_non_robot_entries(self):
        def raises():
            raise Exception
        self._verify_traceback('Traceback \(most recent call last\):\n'
                               '  File ".*", line \d+, in raises\n'
                               '    raise Exception',
                               assert_raises, AssertionError, raises)

    def test_remove_entries_with_lambda_and_multiple_entries(self):
        def raises():
            1/0
        raising_lambda = lambda: raises()
        self._verify_traceback('Traceback \(most recent call last\):\n'
                               '  File ".*", line \d+, in <lambda.*>\n'
                               '    raising_lambda = lambda: raises\(\)\n'
                               '  File ".*", line \d+, in raises\n'
                               '    1/0',
                               assert_raises, AssertionError, raising_lambda)

    def test_only_robot_entries(self):
        self._verify_traceback('Traceback \(most recent call last\):\n'
                               '  None',
                               assert_equals, 1, 2)

    def _verify_traceback(self, expected, method, *args):
        try:
            method(*args)
        except Exception:
            type, value, tb = sys.exc_info()
            # first tb entry originates from this file and must be excluded
            traceback = PythonErrorDetails(type, value, tb.tb_next).traceback
        else:
            raise AssertionError
        if not re.match(expected, traceback):
            raise AssertionError('\nExpected:\n%s\n\nActual:\n%s' % (expected, traceback))


if __name__ == "__main__":
    unittest.main()
