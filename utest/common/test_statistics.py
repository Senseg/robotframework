import unittest
import sys

from robot import utils
from robot.utils.asserts import *
from robot.common.statistics import *
from robot.common.model import _Critical, BaseTestCase
from robot.errors import DataError


class SuiteMock:

    def __init__(self, name='My Name', crit_tags=None):
        self.name = name
        self.critical = _Critical(crit_tags)
        self.suites = []
        self.tests = []
        self.message = ''

    def get_long_name(self):
        return self.name

    def add_suite(self, name):
        suite = SuiteMock(name, self.critical.tags)
        self.suites.append(suite)
        return suite

    def add_test(self, status, tags=None):
        test = TestMock(status, tags,
                        self.critical.are_critical(tags or []))
        self.tests.append(test)
        return test


class TestMock(BaseTestCase):

    def __init__(self, status='PASS', tags=None, critical=True):
        self.status = status
        self.tags = tags is not None and tags or []
        self.critical = critical and 'yes' or 'no'
        self.name = ''


def verify_stat(stat, name, passed, failed, critical=None, non_crit=None):
    assert_equals(stat.name, name, 'stat.name')
    assert_equals(stat.passed, passed)
    assert_equals(stat.failed, failed)
    if critical is not None:
        assert_equals(stat.critical, critical)
    if non_crit is not None:
        assert_equals(stat.non_critical, non_crit)

def verify_suite(suite, name, crit_pass, crit_fail, all_pass=None, all_fail=None):
    verify_stat(suite.critical, name, crit_pass, crit_fail)
    if all_pass is None:
        all_pass, all_fail = crit_pass, crit_fail
    verify_stat(suite.all, name, all_pass, all_fail)

def generate_default_suite():
    suite = SuiteMock('Root Suite', ['smoke'])
    s1 = suite.add_suite('Root Suite.First Sub Suite')
    s2 = suite.add_suite('Root Suite.Second Sub Suite')
    s11 = s1.add_suite('Root Suite.First Sub Suite.Sub Suite 1_1')
    s12 = s1.add_suite('Root Suite.First Sub Suite.Sub Suite 1_2')
    s13 = s1.add_suite('Root Suite.First Sub Suite.Sub Suite 1_3')
    s21 = s2.add_suite('Root Suite.Second Sub Suite.Sub Suite 2_1')
    s11.add_test('PASS')
    s11.add_test('FAIL', ['t1'])
    s12.add_test('PASS', ['t1','t2',])
    s12.add_test('PASS', ['t1','smoke'])
    s12.add_test('FAIL', ['t1','t2','t3','smoke'])
    s13.add_test('PASS', ['t1','t2','smoke'])
    s21.add_test('FAIL', ['t3','smoke'])
    return suite


class TestStatisticsSimple(unittest.TestCase):

    def setUp(self):
        suite = SuiteMock('Hello')
        suite.tests = [TestMock('PASS'), TestMock('PASS'), TestMock('FAIL')]
        self.statistics = Statistics(suite)

    def test_total(self):
        verify_stat(self.statistics.total.critical, 'Critical Tests', 2, 1)
        verify_stat(self.statistics.total.all, 'All Tests', 2, 1)

    def test_suite(self):
        verify_suite(self.statistics.suite, 'Hello', 2, 1)

    def test_tags(self):
        assert_equals(self.statistics.tags.stats, {})


class TestStatisticsNotSoSimple(unittest.TestCase):

    def setUp(self):
        self.statistics = Statistics(generate_default_suite())

    def test_total(self):
        verify_stat(self.statistics.total.all, 'All Tests', 4, 3)
        verify_stat(self.statistics.total.critical, 'Critical Tests', 2, 2)

    def test_suite(self):
        suite = self.statistics.suite
        verify_suite(suite, 'Root Suite', 2, 2, 4, 3)
        assert_equals(len(suite.suites), 2)
        s1, s2 = suite.suites
        verify_suite(s1, 'Root Suite.First Sub Suite', 2, 1, 4, 2)
        verify_suite(s2, 'Root Suite.Second Sub Suite', 0, 1, 0, 1)
        assert_equals(len(s1.suites), 3)
        s11, s12, s13 = s1.suites
        pre  ='Root Suite.First Sub Suite.'
        verify_suite(s11, pre+'Sub Suite 1_1', 0, 0, 1, 1)
        verify_suite(s12, pre+'Sub Suite 1_2', 1, 1, 2, 1)
        verify_suite(s13, pre+'Sub Suite 1_3', 1, 0, 1, 0)
        assert_equals(len(s2.suites), 1)
        s21 = s2.suites[0]
        pre  ='Root Suite.Second Sub Suite.'
        verify_suite(s21, pre+'Sub Suite 2_1', 0, 1, 0, 1)

    def test_tags(self):
        tags = self.statistics.tags
        keys = tags.stats.keys()
        assert_equals(len(keys), 4)
        keys.sort()
        assert_equals(keys, 'smoke t1 t2 t3'.split())
        verify_stat(tags.stats['smoke'], 'smoke', 2, 2, True, False)
        verify_stat(tags.stats['t1'], 't1', 3, 2, False, False)
        verify_stat(tags.stats['t2'], 't2', 2, 1, False, False)
        verify_stat(tags.stats['t3'], 't3', 0, 2, False, False)


_incl_excl_data = [
    ([], []),
    ([], ['t1','t2']),
    (['t1'], ['t1','t2']),
    (['t1','t2'], ['t1','t2','t3','t4']),
    (['UP'], ['t1','t2','up']),
    (['not','not2'], ['t1','t2','t3']),
    (['t*'], ['t1','s1','t2','t3','s2','s3']),
    (['T*','r'], ['t1','t2','r','teeeeeeee']),
    (['*'], ['t1','t2','s1','tag']),
    (['t1','t2','t3','not'], ['t1','t2','t3','t4','s1','s2'])
]


class TestTagStatistics(unittest.TestCase):

    def test_include(self):
        for incl, tags in _incl_excl_data:
            tagstats = TagStatistics(incl, [])
            tagstats.add_test(TestMock('PASS', tags), _Critical())
            exp_keys = [tag for tag in sorted(tags)
                        if incl == [] or utils.matches_any(tag, incl)]
            assert_equal(sorted(tagstats.stats.keys()),
                         exp_keys, "Incls: %s " % incl)

    def test_exclude(self):
        for excl, tags in _incl_excl_data:
            tagstats = TagStatistics([], excl)
            tagstats.add_test(TestMock('PASS', tags), _Critical())
            exp_keys = [tag for tag in sorted(tags)
                        if not utils.matches_any(tag, excl)]
            assert_equal(sorted(tagstats.stats.keys()),
                         exp_keys, "Excls: %s" % excl)

    def test_include_and_exclude(self):
        for incl, excl, tags, exp in [
               ([], [], ['t0','t1','t2'], ['t0','t1','t2']),
               (['t1'], ['t2'], ['t0','t1','t2'], ['t1']),
               (['t?'], ['t2'], ['t0','t1','t2','x'], ['t0','t1']),
               (['t?'], ['*2'], ['t0','t1','t2','x2'], ['t0','t1']),
               (['t1','t2'], ['t2'], ['t0','t1','t2'], ['t1']),
               (['t1','t2','t3','not'], ['t2','t0'],
                ['t0','t1','t2','t3','x'], ['t1','t3'] )
              ]:
            tagstats = TagStatistics(incl, excl)
            tagstats.add_test(TestMock('PASS', tags), _Critical())
            assert_equal(sorted(tagstats.stats.keys()),
                         exp, "Incls: %s, Excls: %s" % (incl, excl))

    def test_combine_with_name(self):
        for comb_tags, expected_name in [
                ([], '' ),
                ([('t1&t2', 'my name')], 'my name'),
                ([('t1NOTt3', 'Others')], 'Others'),
                ([('1:2&2:3', 'nAme')], 'nAme'),
                ([('3*', '')], '3*' ),
                ([('4NOT5', 'Some new name')], 'Some new name')
               ]:
            stats = TagStatistics(combine=comb_tags)
            test = TestMock()
            stats._add_combined_statistics(test)
            assert_equals(len(stats.stats), expected_name != '')
            if expected_name:
                assert_equals(stats.stats[expected_name].name, expected_name)

    def test_is_combined_with_and_statements(self):
        for comb_tags, test_tags, expected_count in [
                ('t1', ['t1'], 1),
                ('t1', ['t2'], 0),
                ('t1&t2', ['t1'], 0),
                ('t1&t2', ['t1','t2'], 1),
                ('t1&t2', ['T1','t 2','t3'], 1),
                ('t*', ['s','t','u'], 1),
                ('t*', ['s','tee','t'], 1),
                ('t*&s', ['s','tee','t'], 1),
                ('t*&s&non', ['s','tee','t'], 0)
               ]:
            self._test_combined_statistics(comb_tags, test_tags, expected_count)

    def _test_combined_statistics(self, comb_tags, test_tags, expected_count):
            stats = TagStatistics(combine=[(comb_tags, 'name')])
            test = TestMock(tags=test_tags)
            stats._add_combined_statistics(test)
            assert_equals(len(stats.stats['Name'].tests), expected_count,
                          'comb: %s, test: %s' % (comb_tags, test_tags))

    def test_is_combined_with_not_statements(self):
        stats = TagStatistics()
        for comb_tags, test_tags, expected_count in [
                ('t1NOTt2', [], 0),
                ('t1NOTt2', ['t1'], 1),
                ('t1NOTt2', ['t1','t2'], 0),
                ('t1NOTt2', ['t3'], 0),
                ('t1NOTt2', ['t3','t2'], 0),
                ('t*NOTt2', ['t1'], 1),
                ('t*NOTt2', ['t'], 1),
                ('t*NOTt2', ['TEE'], 1),
                ('t*NOTt2', ['T2'], 0),
                ('T*NOTT?', ['t'], 1),
                ('T*NOTT?', ['tt'], 0),
                ('T*NOTT?', ['ttt'], 1),
                ('T*NOTT?', ['tt','t'], 0),
                ('T*NOTT?', ['ttt','something'], 1),
                ('tNOTs*NOTr', ['t'], 1),
                ('tNOTs*NOTr', ['t','s'], 0),
                ('tNOTs*NOTr', ['R','T'], 0),
                ('tNOTs*NOTr', ['R','T','s'], 0),
               ]:
            self._test_combined_statistics(comb_tags, test_tags, expected_count)

    def test_combine(self):
        # This is more like an acceptance test than a unit test ...
        for comb_tags, comb_matches, tests_tags, crit_tags in [
                (['t1&t2'], [1], [['t1','t2','t3'],['t1','t3']], []),
                (['1&2&3'], [2], [['1','2','3'],['1','2','3','4']], ['1','2']),
                (['1&2','1&3'], [1,2], [['1','2','3'],['1','3'],['1']], ['1']),
                (['t*'], [3], [['t1','x','y'],['tee','z'],['t']], ['x']),
                (['t?&s'], [2], [['t1','s'],['tt','s','u'],['tee','s'],['s']], []),
                (['t*&s','*'], [2,3], [['s','t','u'],['tee','s'],[],['x']], []),
                (['tNOTs'], [1], [['t','u'],['t','s']], []),
                (['tNOTs','t&s','tNOTsNOTu', 't&sNOTu'], [3,2,2,1],
                  [['t','u'],['t','s'],['s','t','u'],['t'],['t','v']], ['t']),
                (['nonex'], [0], [['t1'],['t1,t2'],[]], [])
               ]:
            # 1) Create tag stats
            tagstats = TagStatistics(combine=[(t, '') for t in comb_tags])
            all_tags = []
            for tags in tests_tags:
                tagstats.add_test(TestMock('PASS', tags), _Critical(crit_tags))
                all_tags.extend(tags)
            # 2) Actual values
            names = [stat.name for stat in sorted(tagstats.stats.values())]
            # 3) Expected values
            exp_crit = []; exp_noncr = []; exp_comb = []
            for tag in utils.normalize_tags(all_tags):
                if tag in crit_tags:
                    exp_crit.append(tag)
                else:
                    exp_noncr.append(tag)
            for comb, count in zip(comb_tags, comb_matches):
                exp_comb.append(comb)
                try:
                    assert_equals(len(tagstats.stats[comb].tests), count)
                except KeyError:
                    fail("No key %s. Stats: %s" % (comb, tagstats.stats))
            exp_names = exp_crit + sorted(exp_comb) + exp_noncr
            # 4) Verify names (match counts were already verified)
            assert_equals(names, exp_names)

    def test_through_suite(self):
        suite = generate_default_suite()
        suite.critical_tags = ['smoke']
        statistics = Statistics(suite, -1, ['t*','smoke'], ['t3'],
                                [('t1 & t2', ''), ('t? & smoke', ''),
                                 ('t1 NOT t2', ''), ('none & t1', 'a title')])
        stats = sorted(statistics.tags.stats.values())
        expected = [('smoke', 4), ('a title', 0), ('t1 & t2', 3),
                    ('t1 NOT t2', 2), ('t? & smoke', 4), ('t1', 5), ('t2', 3)]
        names = [stat.name for stat in stats]
        exp_names = [name for name, count in expected]
        assert_equals(names, exp_names)
        for name, count in expected:
            assert_equals(len(statistics.tags.stats[name].tests), count, name)


class TestTagStatLink(unittest.TestCase):

    def test_valid_string_is_parsed_correctly(self):
        for arg, exp in [(('Tag', 'bar/foo.html', 'foobar'),
                          ('^Tag$', 'bar/foo.html', 'foobar')),
                         (('hello', 'gopher://hello.world:8090/hello.html',
                           'Hello World'),
                          ('^hello$', 'gopher://hello.world:8090/hello.html',
                           'Hello World'))]:
            link = TagStatLink(*arg)
            assert_equal(exp[0], link._regexp.pattern)
            assert_equal(exp[1], link._link)
            assert_equal(exp[2], link._title)

    def test_valid_string_containing_patterns_is_parsed_correctly(self):
        for arg, exp_pattern in [('*', '^(.*)$'), ('f*r', '^f(.*)r$'),
                                 ('*a*', '^(.*)a(.*)$'),  ('?', '^(.)$'),
                                 ('??', '^(..)$'), ('f???ar', '^f(...)ar$'),
                                 ('F*B?R*?', '^F(.*)B(.)R(.*)(.)$')]:
            link = TagStatLink(arg, 'some_url', 'some_title')
            assert_equal(exp_pattern, link._regexp.pattern)

    def test_underscores_in_title_are_converted_to_spaces(self):
        link = TagStatLink('', '', 'my_name')
        assert_equal(link._title, 'my name')

    def test_get_link_returns_correct_link_when_matches(self):
        for arg, exp in [(('smoke', 'http://tobacco.com', 'Lung_cancer'),
                          ('http://tobacco.com', 'Lung cancer')),
                         (('tag', 'ftp://foo:809/bar.zap', 'Foo_in a Bar'),
                          ('ftp://foo:809/bar.zap', 'Foo in a Bar'))]:
            link = TagStatLink(*arg)
            assert_equals(exp, link.get_link(arg[0]))

    def test_get_link_returns_none_when_no_match(self):
        link = TagStatLink('smoke', 'http://tobacco.com', 'Lung cancer')
        for tag in ['foo', 'b a r', 's moke']:
            assert_none(link.get_link(tag))

    def test_pattern_matches_case_insensitively(self):
        exp = 'http://tobacco.com', 'Lung cancer'
        link = TagStatLink('smoke', *exp)
        for tag in ['Smoke', 'SMOKE', 'smoke']:
            assert_equals(exp, link.get_link(tag))

    def test_pattern_matches_when_spaces(self):
        exp = 'http://tobacco.com', 'Lung cancer'
        link = TagStatLink('smoking kills', *exp)
        for tag in ['Smoking Kills', 'SMOKING KILLS']:
            assert_equals(exp, link.get_link(tag))

    def test_pattern_match(self):
        link = TagStatLink('f?o*r', 'http://foo/bar.html', 'FooBar')
        for tag in ['foobar', 'foor', 'f_ofoobarfoobar', 'fOoBAr']:
            assert_equal(link.get_link(tag), ('http://foo/bar.html', 'FooBar'))

    def test_pattern_substitution_with_one_match(self):
        link = TagStatLink('tag-*', 'http://tracker/?id=%1', 'Tracker')
        for id in ['1', '23', '456']:
            exp = ('http://tracker/?id=%s' % id, 'Tracker')
            assert_equal(exp, link.get_link('tag-%s' % id))

    def test_pattern_substitution_with_multiple_matches(self):
        link = TagStatLink('?-*', 'http://tracker/?id=%1-%2', 'Tracker')
        for id1, id2 in [('1', '2'), ('3', '45'), ('f', 'bar')]:
            exp = ('http://tracker/?id=%s-%s' % (id1, id2), 'Tracker')
            assert_equal(exp, link.get_link('%s-%s' % (id1, id2)))

    def test_pattern_substitution_with_multiple_substitutions(self):
        link = TagStatLink('?-?-*', '%3-%3-%1-%2-%3', 'Tracker')
        assert_equal(link.get_link('a-b-XXX'), ('XXX-XXX-a-b-XXX', 'Tracker'))

    def test_matches_are_ignored_in_pattern_substitution(self):
        link = TagStatLink('?-*-*-?', '%4-%2-%2-%4', 'Tracker')
        assert_equal(link.get_link('A-XXX-ABC-B'), ('B-XXX-XXX-B', 'Tracker'))


class TestTagStatLinks(unittest.TestCase):

    def test_tag_stat_links_with_valid_tags(self):
        values = [('1', '2', '3'), ('tag', 'foo.html', 'bar')]
        tag_stat_links = TagStatInfo([], values)
        assert_equal(len(tag_stat_links._links), 2)


if __name__ == "__main__":
    unittest.main()
