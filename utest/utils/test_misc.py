import os
import unittest
import sys

from robot.utils.asserts import assert_equals
from robot import utils
if utils.is_jython:
    import JavaExceptions

from robot.utils.misc import seq2str, get_link_path, printable_name, \
    printable_name_from_path, calc_percents, percents_to_widths, _remove_prefix


class TestMiscUtils(unittest.TestCase):

    def test_seq2str(self):
        for exp, seq in [ ( "", () ),
                          ( "'One'", ("One",) ),
                          ( "'1' and '2'", ("1","2") ),
                          ( "'1', '2', '3', 'f o u r', 'fi ve' and '6'",
                            ("1","2","3","f o u r","fi ve","6") ) ]:
            assert_equals(exp, seq2str(seq))

    def test_get_link_path(self):
        if os.sep == '/':
            inputs = [
                ( '/tmp/', '/tmp/bar.txt', 'bar.txt' ),
                ( '/tmp', '/tmp/x/bar.txt', 'x/bar.txt' ),
                ( '/tmp/', '/tmp/x/y/bar.txt', 'x/y/bar.txt' ),
                ( '/tmp/', '/tmp/x/y/z/bar.txt', 'x/y/z/bar.txt' ),
                ( '/tmp', '/x/y/z/bar.txt', '../x/y/z/bar.txt' ),
                ( '/tmp/', '/x/y/z/bar.txt', '../x/y/z/bar.txt' ),
                ( '/tmp', '/x/bar.txt', '../x/bar.txt' ),
                ( '/tmp', '/x/y/z/bar.txt', '../x/y/z/bar.txt' ),
                ( '/', '/x/bar.txt', 'x/bar.txt' ),
                ( '/path/to', '/path/to/result_in_same_dir.html', 'result_in_same_dir.html' ),
                ( '/path/to/dir', '/path/to/result_in_parent_dir.html', '../result_in_parent_dir.html' ),
                ( '/path/to', '/path/to/dir/result_in_sub_dir.html', 'dir/result_in_sub_dir.html' ),
                ( '/commonprefix/sucks/baR', '/commonprefix/sucks/baZ.txt', '../baZ.txt' ),
                ( '/a/very/long/path', '/no/depth/limitation', '../../../../no/depth/limitation' ),
                ( '/etc/hosts', '/path/to/existing/file', '../path/to/existing/file' ),
                ( '/path/to/identity', '/path/to/identity', 'identity' ),
            ]
        else:
            inputs = [
                ( 'c:\\temp\\', 'c:\\temp\\bar.txt', 'bar.txt' ),
                ( 'c:\\temp', 'c:\\temp\\x\\bar.txt', 'x/bar.txt' ),
                ( 'c:\\temp\\', 'c:\\temp\\x\\y\\bar.txt', 'x/y/bar.txt' ),
                ( 'c:\\temp', 'c:\\temp\\x\\y\\z\\bar.txt',
                  'x/y/z/bar.txt' ),
                ( 'c:\\temp\\', 'c:\\x\\y\\bar.txt', '../x/y/bar.txt' ),
                ( 'c:\\temp', 'c:\\x\\y\\bar.txt', '../x/y/bar.txt' ),
                ( 'c:\\temp', 'c:\\x\\bar.txt', '../x/bar.txt' ),
                ( 'c:\\temp', 'c:\\x\\y\\z\\bar.txt', '../x/y/z/bar.txt' ),
                ( 'c:\\temp\\', 'r:\\x\\y\\bar.txt', 'file:///r:/x/y/bar.txt' ),
                ( 'c:\\', 'c:\\x\\bar.txt', 'x/bar.txt' ),
                ( 'c:\\path\\to', 'c:\\path\\to\\result_in_same_dir.html', 'result_in_same_dir.html' ),
                ( 'c:\\path\\to\\dir', 'c:\\path\\to\\result_in_parent_dir.html', '../result_in_parent_dir.html' ),
                ( 'c:\\path\\to', 'c:\\path\\to\\dir\\result_in_sub_dir.html', 'dir/result_in_sub_dir.html' ),
                ( 'c:\\commonprefix\\sucks\\baR', 'c:\\commonprefix\\sucks\\baZ.txt', '../baz.txt' ),
                ( 'c:\\a\\very\\long\\path', 'c:\\no\\depth\\limitation', '../../../../no/depth/limitation' ),
                ( 'c:\\boot.ini', 'c:\\path\\to\\existing\\file', 'path/to/existing/file' ),
                ( 'c:\\path\\to\\identity', 'c:\\path\\to\\identity', 'identity' ),
            ]
        import robot.utils.normalizing
        for basedir, target, expected in inputs:
            if robot.utils.normalizing._CASE_INSENSITIVE_FILESYSTEM :
                expected = expected.lower()
            assert_equals(get_link_path(target, basedir).replace('R:', 'r:'), expected,
                         '%s -> %s' % (target, basedir))

    def test_get_link_path_with_unicode(self):
        assert_equals(get_link_path(u'\xe4\xf6.txt', ''),'%C3%A4%C3%B6.txt')

    def test_printable_name_from_path(self):
        paths_and_names = [ ('tests.html', 'Tests'),
                            ('my tests.html', 'My Tests'),
                            ('your_tests', 'Your Tests'),
                            ('TESTS.HTML', 'TESTS'),
                            ('camelCaseTests', 'Camel Case Tests'),
                            ('MoreCAMELCase', 'More CAMEL Case'),
                            ('some_set_of_tests', 'Some Set Of Tests'),
                            ('1_more test_set here ', '1 More Test Set Here') ]
        if os.sep == '/':
            paths_and_names += [ ('/path/to/tests.py', 'Tests'),
                                 ('/path/to/Tests', 'Tests' ),
                                 ('/path_to/my_tests/', 'My Tests' ) ]
        else:
            paths_and_names += [ ('c:\\path\\to\\tests.py', 'Tests'),
                                 ('c:\\path\\to\\Tests', 'Tests'),
                                 ('c:\\path_to\\my_tests\\', 'My Tests') ]
        for path, expected in paths_and_names:
            actual = printable_name_from_path(path)
            assert_equals(expected, actual, path)

    def test_printable_name(self):
        for inp, exp in [ ('simple', 'Simple'),
                          ('ALLCAPS', 'ALLCAPS'),
                          ('name with spaces', 'Name With Spaces'),
                          ('more   spaces', 'More Spaces'),
                          ('Cases AND spaces', 'Cases AND Spaces'),
                          ('under_Score_name', 'Under_Score_name'),
                          ('camelCaseName', 'CamelCaseName'),
                          ('with89numbers', 'With89numbers'),
                          ('with 89 numbers', 'With 89 Numbers'),
                          ('', '') ]:
            assert_equals(printable_name(inp), exp)

    def test_printable_name_with_code_style(self):
        for inp, exp in [ ('simple', 'Simple'),
                          ('ALLCAPS', 'ALLCAPS'),
                          ('under_score_name', 'Under Score Name'),
                          ('under_score and spaces', 'Under Score And Spaces'),
                          ('miXed_CAPS_nAMe', 'MiXed CAPS NAMe'),
                          ('camelCaseName', 'Camel Case Name'),
                          ('camelCaseWithDigit1', 'Camel Case With Digit 1'),
                          ('name42WithNumbers666', 'Name 42 With Numbers 666'),
                          ('12more34numbers', '12 More 34 Numbers'),
                          ('mixedCAPSCamelName', 'Mixed CAPS Camel Name'),
                          ('foo-bar', 'Foo-bar'),
                          ('','') ]:
            assert_equals(printable_name(inp, code_style=True), exp)

    def test_remove_prefix(self):
        for inp, exp in [ ('01__hello', 'hello'),
                          ('textual_prefix__hello', 'hello'),
                          ('01__actual__name.tsv', 'actual__name.tsv'),
                          ('no_prefix_here.html', 'no_prefix_here.html') ]:
            assert_equals(_remove_prefix(inp), exp)

    def test_calc_percents_zeros(self):
        assert_equals(calc_percents(0, 0), (0, 0))

    def test_calc_percents_below_limit(self):
        for in1, in2 in [ (1, 9999), (2, 9998), (9, 9991), (1244, 145431435) ]:
            assert_equals(calc_percents(in1, in2), (0.1, 99.9))
            assert_equals(calc_percents(in2, in1), (99.9, 0.1))

    def test_calc_percents_one_zero(self):
        for count in [ 1, 2, 10, 42, 100, 1234, 999999999 ]:
            assert_equals(calc_percents(count, 0), (100.0, 0))
            assert_equals(calc_percents(0, count), (0, 100.0))

    def test_calc_percents_same(self):
        for count in [ 1, 2, 10, 42, 100, 1234, 999999999 ]:
            assert_equals(calc_percents(count, count), (50.0, 50.0))

    def test_calc_percents_no_rounding(self):
        for in1, in2, ex1, ex2 in [ (3, 1, 75.0, 25.0),
                                    (99, 1, 99.0, 1.0),
                                    (999, 1, 99.9, 0.1),
                                    (87, 13, 87.0, 13.0),
                                    (601, 399, 60.1, 39.9),
                                    (857, 143, 85.7, 14.3) ]:
            assert_equals(calc_percents(in1, in2), (ex1, ex2))
            assert_equals(calc_percents(in2, in1), (ex2, ex1))

    def test_calc_percents_rounding(self):
        for in1, in2, ex1, ex2 in [ (2, 1, 66.7, 33.3),
                                    (6, 1, 85.7, 14.3),
                                    (3, 8, 27.3, 72.7),
                                    (5, 4, 55.6, 44.4),
                                    (28, 2, 93.3, 6.7),
                                    (70, 1, 98.6, 1.4),
                                    (999, 2, 99.8, 0.2),
                                    (7778, 2222, 77.8, 22.2) ]:
            assert_equals(calc_percents(in1, in2), (ex1, ex2))
            assert_equals(calc_percents(in2, in1), (ex2, ex1))

    def test_calc_percents_rounding_both_up(self):
        for in1, in2, ex1, ex2 in [ (3, 13, 18.8, 81.3),
                                    (105, 9895, 1.1, 99.0),
                                    (4445, 5555, 44.5, 55.6) ]:
            assert_equals(calc_percents(in1, in2), (ex1, ex2))
            assert_equals(calc_percents(in2, in1), (ex2, ex1))

    def test_percentages_to_widths_zeros(self):
        self._verify_percentages_to_widths(0.0, 0.0)

    def test_percentages_to_widths_no_changes(self):
        for in1, in2 in [ (0.0, 100.0),
                          (1.0, 99.0),
                          (33.3, 66.7),
                          (50.0, 50.0) ]:
            self._verify_percentages_to_widths(in1, in2)
            self._verify_percentages_to_widths(in2, in1)

    def test_percentages_to_widths_below_limit(self):
        for in1, in2 in [ (0.1, 99.9), (0.2, 99.8), (0.9, 99.1) ]:
            self._verify_percentages_to_widths(in1, in2, 1.0, 99.0)
            self._verify_percentages_to_widths(in2, in1, 99.0, 1.0)

    def test_percentages_to_widths_when_both_rounded_up(self):
        for in1, in2, ex1, ex2 in [ (1.1, 99.0, 1.1, 98.9),
                                    (18.8, 81.3, 18.8, 81.2),
                                    (44.5, 55.6, 44.5, 55.5),
                                    (50.0, 50.1, 50.0, 50.0) ]:
            self._verify_percentages_to_widths(in1, in2, ex1, ex2)
            self._verify_percentages_to_widths(in2, in1, ex2, ex1)

    def _verify_percentages_to_widths(self, inp1, inp2, exp1=None, exp2=None):
        act1, act2 = percents_to_widths(inp1, inp2)
        if exp1 is None:
            exp1, exp2 = inp1, inp2
        if exp1 + exp2 > 0:
            if exp1 > exp2:
                exp1 -= 0.01
            else:
                exp2 -= 0.01
        inp_msg = ' with inputs (%s, %s)' % (inp1, inp2)
        assert_equals(act1, exp1, 'Wrong pass percentage' + inp_msg)
        assert_equals(act2, exp2, 'Wrong fail percentage' + inp_msg)


if __name__ == "__main__":
    unittest.main()
