import unittest
import sys

from robot.utils.match import *


class TestMatch(unittest.TestCase):

    def test_eq(self):
        assert eq("foo", "foo")
        assert eq("f OO\t\n", "  foo", caseless=True, spaceless=True)
        assert eq("-a-b-c-", "b", ignore=("-","a","c"))
        assert not eq("foo", "bar")
        assert not eq("foo", "FOO", caseless=False)
        assert not eq("foo", "foo ", spaceless=False)

    def test_eq_any(self):
        assert eq_any("foo", [ "a", "b", " F O O  " ], caseless=True, spaceless=True)
        assert not eq_any("foo", [ "f o o ", "hii", "hoo", "huu", "FOO" ],
                          caseless=False, spaceless=False)

    def test_matches_with_string(self):
        for pattern in ['abc','ABC','*','a*','*C','a*c','*a*b*c*','AB?','???',
                        '?b*','*abc','abc*','*abc*']:
            assert matches('abc',pattern), pattern
        for pattern in ['def','?abc','????','*ed','b*' ]:
            assert not matches('abc',pattern), pattern

    def test_matches_with_multiline_string(self):
        for pattern in ['*', 'multi*string', 'multi?line?string', '*\n*']:
            assert matches('multi\nline\nstring', pattern, spaceless=False), pattern

    def test_matches_with_slashes(self):
        for pattern in ['a*','aa?b*','*c','?a?b?c']:
            assert matches('aa/b\\c', pattern), pattern

    def test_matches_no_pattern(self):
        for string in [ 'foo', '', ' ', '      ', 'what ever',
                        'multi\nline\string here', '=\\.)(/23.',
                        'forw/slash/and\\back\\slash' ]:
            assert matches(string, string), string

    def test_matches_any(self):
        assert matches_any('abc', ['asdf','foo','*b?'])
        assert matches_any('abc', ['*','asdf','foo','*b?'])
        assert not matches_any('abc', ['asdf','foo','*c?'])


if __name__ == "__main__":
    unittest.main()
