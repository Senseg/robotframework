import unittest
from StringIO import StringIO

from robot.parsing.datareader import FromFilePopulator, DataRow
from robot.parsing.model import TestCaseFile
from robot.utils.asserts import assert_equals, assert_true, assert_false

from robot.output import LOGGER
LOGGER.disable_message_cache()


class _MockLogger(object):
    def __init__(self):
        self._output = StringIO()

    def message(self, msg):
        self._output.write(msg.message)

    def value(self):
        return self._output.getvalue()

class _PopulatorTest(unittest.TestCase):

    def _start_table(self, name):
        if isinstance(name, basestring):
            name = [name]
        return self._populator.start_table(name)

    def _create_table(self, name, rows, eof=True):
        self._start_table(name)
        for r  in rows:
            self._populator.add(r)
        if eof:
            self._populator.eof()

    def _assert_setting(self, name, exp_value, exp_comment=None):
        setting = self._setting_with(name)
        assert_equals(setting.value, exp_value)
        self._assert_comment(setting, exp_comment)

    def _assert_fixture(self, fixture_name, exp_name, exp_args, exp_comment=None):
        fixture = self._setting_with(fixture_name)
        self._assert_name_and_args(fixture, exp_name, exp_args)
        self._assert_comment(fixture, exp_comment)

    def _assert_import(self, index, exp_name, exp_args, exp_comment=None):
        imp = self._datafile.setting_table.imports[index]
        self._assert_name_and_args(imp, exp_name, exp_args)
        self._assert_comment(imp, exp_comment)

    def _assert_name_and_args(self, item, exp_name, exp_args):
        assert_equals(item.name, exp_name)
        assert_equals(item.args, exp_args)

    def _assert_meta(self, index, exp_name, exp_value, exp_comment=None):
        meta = self._setting_with('metadata')[index]
        assert_equals(meta.name, exp_name)
        assert_equals(meta.value, exp_value)
        self._assert_comment(meta, exp_comment)

    def _assert_variable(self, index, exp_name, exp_value, exp_comment=None):
        var = self._datafile.variable_table.variables[index]
        assert_equals(var.name, exp_name)
        assert_equals(var.value, exp_value)
        self._assert_comment(var, exp_comment)

    def _assert_comment(self, item, exp_comment):
        if exp_comment:
            assert_equals(item.comment, exp_comment)

    def _setting_with(self, name):
        return getattr(self._datafile.setting_table, name)

    def _nth_test(self, index):
        return self._datafile.testcase_table.tests[index-1]

    def _first_test(self):
        return self._nth_test(1)

    def _number_of_steps_should_be(self, test, expected_steps):
        assert_equals(len(test.steps), expected_steps)


class TestCaseFilePopulatingTest(_PopulatorTest):

    def setUp(self):
        self._datafile = TestCaseFile()
        self._datafile.directory = '/path/to'
        self._populator = FromFilePopulator(self._datafile)
        self._logger = _MockLogger()
        self._console_logger = LOGGER._loggers.pop(0)
        LOGGER.register_logger(self._logger)

    def tearDown(self):
        LOGGER.unregister_logger(self._logger)
        LOGGER._loggers.insert(0, self._console_logger)

    def test_starting_valid_table(self):
        for name in ['Test Cases', '  variables   ', 'K E Y WO R D S']:
            assert_true(self._start_table(name))

    def test_table_headers(self):
        header_list = ['seTTINGS', 'header', 'again']
        self._create_table(header_list,[])
        setting_table = self._datafile.setting_table
        assert_equals(setting_table.header, header_list)
        assert_equals(setting_table.name, header_list[0])

    def test_starting_invalid_table(self):
        assert_false(self._start_table('Per Se'))

    def test_adding_empty_row_should_not_fail(self):
        self._create_table('Settings', [[]])

    def test_adding_settings(self):
        doc = 'This is doc'
        template = 'Foo'
        more_doc = 'smore'
        force_tags = 'force'
        more_tags = 'more tagness'
        even_more_tags = 'even more'
        default_tags = 'default'
        setup_name, setup_args = 'Keyword Name', ['a1', 'a2']
        self._create_table('Settings', [['Documentation', doc],
                                        ['S  uite Tear Down'] + [setup_name],
                                        ['S  uite SeTUp'] + [setup_name],
                                        ['...'] + setup_args,
                                        ['S  uite teardown'] + setup_args,
                                        ['Doc um entati on', more_doc],
                                        ['force tags', force_tags],
                                        ['Default tags', default_tags],
                                        ['FORCETAGS', more_tags],
                                        ['test timeout', '1s'],
                                        ['De Fault TAGS', more_tags],
                                        ['...', even_more_tags],
                                        ['test timeout', 'timeout message'],
                                        ['test timeout', more_doc],
                                        ['test template', template]
                                        ])
        self._assert_setting('doc', doc + ' ' + more_doc)
        self._assert_fixture('suite_setup', setup_name, setup_args)
        self._assert_fixture('suite_teardown', setup_name, setup_args)
        self._assert_tags('default_tags', [default_tags, more_tags, even_more_tags])
        self._assert_tags('force_tags', [force_tags, more_tags])
        timeout = self._setting_with('test_timeout')
        assert_equals(timeout.value, '1s')
        assert_equals(timeout.message, 'timeout message '+more_doc)
        self._assert_setting('test_template', template)

    def _assert_tags(self, tag_name, exp_value):
        tag = self._setting_with(tag_name)
        assert_equals(tag.value, exp_value)

    def test_continuing_in_the_begining_of_the_setting_table(self):
        self._create_table('Settings', [['...']])
        assert_equals(self._logger.value(), "Invalid syntax in file 'None' in "
                                            "table 'Settings': Non-existing "
                                            "setting '...'.")

    def test_continuing_in_the_begining_of_the_variable_table(self):
        self._create_table('Variables', [['...', 'val']])
        self._assert_variable(0, '...',  ['val'])

    def test_continuing_in_the_begining_of_the_testcase_table(self):
        self._create_table('test cases', [['...', 'foo']])
        assert_equals(self._first_test().name, '...')

    def test_unnamed_testcase(self):
        self._create_table('test cases', [['', 'foo', '#comment'],
                                          ['', '[documentation]', "What's up doc?"]])
        test = self._first_test()
        assert_equals(test.name, '')
        assert_equals(test.doc.value, "What's up doc?")
        assert_equals(test.steps[0].comment, 'comment')

    def test_unnamed_test_and_line_continuation(self):
        self._create_table('test cases', [['', '...', 'foo', '#comment']])
        assert_equals(self._first_test().name, '')
        assert_equals(self._first_test().steps[0].comment, 'comment')

    def test_continuing_in_the_begining_of_the_keyword_table(self):
        self._create_table('keywords', [['...', 'foo']])
        assert_equals(self._nth_uk(1).name, '...')

    def test_invalid_settings(self):
        self._create_table('Settings', [['In valid', 'val ue']])
        assert_equals(self._logger.value(), "Invalid syntax in file 'None' in "
                                            "table 'Settings': Non-existing "
                                            "setting 'In valid'.")

    def test_adding_import(self):
        self._create_table('settings', [['Library', 'FooBarness'],
                                        ['Library', 'BarFooness', 'arg1', 'arg2'],
                                        ['Resource', 'QuuxNess.txt'],
                                        ['Variables', 'varzors.py']])
        assert_equals(len(self._datafile.setting_table.imports), 4)
        self._assert_import(0, 'FooBarness', [])
        self._assert_import(1, 'BarFooness', ['arg1', 'arg2'])
        self._assert_import(2, 'QuuxNess.txt', [])
        self._assert_import(3, 'varzors.py', [])

    def test_suite_metadata(self):
        self._create_table('settings', [['Meta: Foon:ess', 'Barness'],
                                        ['Metadata', 'Quux', 'Value']])
        self._assert_meta(0, 'Foon:ess', 'Barness')
        self._assert_meta(1, 'Quux', 'Value')

    def test_adding_variables(self):
        self._create_table('Variables', [['${scalar}', 'value'],
                                         ['@{list}', 'v1', 'v2'],
                                         ['...', 'v3', 'v4']])
        assert_equals(len(self._datafile.variable_table.variables), 2)
        self._assert_variable(0, '${scalar}', ['value'])
        self._assert_variable(1, '@{list}', ['v1', 'v2', 'v3', 'v4'])

    def test_setting_in_multiple_rows(self):
        self._create_table('Settings', [['Documentation', 'Part 1'],
                                        ['...', 'Part 2']])
        self._assert_setting('doc', 'Part 1 Part 2')

    def test_test_case_populating(self):
        self._create_table('Test cases', [['My test name'],
                                          ['', 'No operation'],
                                          ['Another test'],
                                          ['', 'Log', 'quux']])
        assert_equals(len(self._datafile.testcase_table.tests), 2)
        test = self._first_test()
        assert_equals(len(test.steps), 1)
        assert_equals(test.steps[0].keyword, 'No operation')
        assert_equals(len(self._first_test().steps), 1)

    def test_case_name_and_first_step_on_same_row(self):
        self._create_table('Test cases', [['My test name', 'No Operation']])
        assert_equals(len(self._first_test().steps), 1)

    def test_continuing_row_in_test(self):
        self._create_table('Test cases', [['My test name', 'Log Many', 'foo'],
                                          ['', '...', 'bar', 'quux'],
                                          ['Another test'],
                                          ['', '...'],
                                          ['', 'Log Many', 'quux'],
                                          ['', '...', 'fooness'],
                                          ['', 'Log', 'barness']])
        assert_equals(len(self._first_test().steps), 1)
        assert_equals(len(self._nth_test(2).steps), 3)

    def test_for_loop(self):
        self._create_table('Test cases', [['For loop test'],
                                          ['', ':FOR', '${i}', 'IN', '@{list}'],
                                          ['', '', 'Log', '${i}']])
        assert_equals(len(self._first_test().steps), 1)
        for_loop = self._first_test().steps[0]
        assert_equals(len(for_loop.steps), 1)
        assert_true(not for_loop.range)
        assert_equals(for_loop.vars, ['${i}'])
        assert_equals(for_loop.items, ['@{list}'])

    def test_in_range_for_loop(self):
        self._create_table('Test cases', [['For loop test'],
                                          ['', 'Log', 'Before FOR'],
                                          ['', ': for', '${i}', '${j}', 'IN RANGE', '10'],
                                          ['', '', 'Log', '${i}'],
                                          ['', '', 'Fail', '${j}'],
                                          ['', 'Log', 'Outside FOR']])
        assert_equals(len(self._first_test().steps), 3)
        for_loop = self._first_test().steps[1]
        assert_equals(len(for_loop.steps), 2)
        assert_true(for_loop.range)
        assert_equals(for_loop.vars, ['${i}', '${j}'])

    def test_malicious_for_loop(self):
        self._create_table('Test cases', [['Malicious for loop test'],
                                          ['', 'Log', 'Before FOR'],
                                          ['', '::::   fOr', '${i}', 'IN', '10', '20'],
                                          ['', '...', '30', '40'],
                                          ['', '...', '50', '60'],
                                          ['', '', 'Log Many', '${i}'],
                                          ['', '', '...', '${i}'],
                                          ['', '...', '${i}'],
                                          ['', 'Log', 'Outside FOR']])
        assert_equals(len(self._first_test().steps), 3)
        for_loop = self._first_test().steps[1]
        assert_equals(len(for_loop.steps), 1)
        assert_true(not for_loop.range)
        assert_equals(for_loop.vars, ['${i}'])
        assert_equals(for_loop.items, ['10', '20', '30', '40', '50', '60'])

    def test_for_loop_with_empty_body(self):
        self._create_table('Test cases', [['For loop test'],
                                          ['', ':FOR ', '${var}', 'IN', 'foo'],
                                          ['', 'Log', 'outside FOR']])
        test = self._first_test()
        assert_equals(len(test.steps), 2)
        assert_equals(test.steps[0].steps, [])

    def test_test_settings(self):
        doc = 'This is domumentation for the test case'
        self._create_table('Test cases', [['My test name'],
                                          ['', '[Documentation]', doc],
                                          ['', '[  Tags  ]', 'ankka', 'kameli'],
                                          ['', '... ', '', 'aasi'],
                                          ['', 'Log', 'barness']])
        test = self._first_test()
        assert_equals(len(test.steps), 1)
        assert_equals(test.doc.value, doc)
        assert_equals(test.tags.value, ['ankka', 'kameli', '', 'aasi'])

    def test_invalid_test_settings(self):
        self._create_table('Test cases', [['My test name'],
                                          ['', '[Aasi]']])
        assert_equals(self._logger.value(), "Invalid syntax in file 'None' in "
                                            "table 'Test cases': Invalid syntax "
                                            "in test case 'My test name': "
                                            "Non-existing setting 'Aasi'.")

    def test_test_template_overrides_setting(self):
        setting_test_template = 'Foo'
        test_test_template = 'Bar'
        self._create_table('Settings', [['Test Template', setting_test_template]],
                           eof=False)
        self._create_table('Test Cases', [['','[Template]', test_test_template]])
        test = self._first_test()
        assert_equals(test.template.value, test_test_template)

    def test_invalid_keyword_settings(self):
        self._create_table('Keywords', [['My User Keyword'],
                                        ['', '[ank ka]']])
        assert_equals(self._logger.value(), "Invalid syntax in file 'None' in "
                                            "table 'Keywords': Invalid syntax "
                                            "in keyword 'My User Keyword': "
                                            "Non-existing setting 'ank ka'.")

    def test_creating_user_keywords(self):
        self._create_table('Keywords', [['My User Keyword'],
                                        ['', '[Arguments]', '${foo}', '${bar}'],
                                        ['', 'Log Many', '${foo}'],
                                        ['', '...', 'bar'],
                                        ['', 'No Operation'],
                                        ['', '[Return]', 'ankka', 'kameli']])
        uk = self._nth_uk(0)
        assert_equals(len(uk.steps), 2)
        assert_equals(uk.args.value, ['${foo}', '${bar}'])
        assert_equals(uk.return_.value, ['ankka', 'kameli'])

    def test_curdir_handling(self):
        self._create_table('Test cases', [['My test name'],
                                          ['', 'Log', '${CURDIR}']])
        assert_equals(self._first_test().steps[0].args,
                      [self._datafile.directory])

    def test_turn_off_curdir_handling(self):
        from robot.parsing import datareader
        datareader.PROCESS_CURDIR = False
        self.setUp()
        self._create_table('Test cases', [['My test name'],
                                          ['', 'Log', '${CURDIR}']])
        assert_equals(self._first_test().steps[0].args, ['${CURDIR}'])
        datareader.PROCESS_CURDIR = True

    def test_whitespace_is_ignored(self):
        self._create_table('Test Cases', [['My   test'],
                                          [' ', '[Tags]', 'foo', '  \t  '],
                                          ['  '],
                                          [ '\t'],
                                          ['', 'Log Many', '', 'argh']])
        test = self._first_test()
        assert_equals(test.name, 'My test')
        self._number_of_steps_should_be(test, 1)
        assert_equals(test.tags.value, ['foo'])

    def test_escaping_empty_cells(self):
        self._create_table('Settings', [['Documentation', '\\']],)
        self._assert_setting('doc', '')
        self._create_table('Test cases', [['test',
                                           '', 'Log Many', 'foo', '\\']],)
        assert_equals(self._first_test().steps[0].args, ['Log Many', 'foo', ''])

    def test_populator_happy_path_workflow(self):
        self._create_table('settings', [['Library', 'FooBarness']], eof=False)
        self._create_table('Variables', [['${scalar}', 'value']], eof=False)
        self._create_table('Test cases', [['My test name'],
                                          ['', 'Log', 'quux']], eof=False)
        self._create_table('More cases', [['My other test name'],
                                          ['', 'Log', 'foox']], eof=False)
        self._create_table('Keywords', [['My User Keyword'],
                                        ['', 'Foo', 'Bar']], eof=False)
        self._populator.eof()
        self._assert_import(0, 'FooBarness', [])
        assert_equals(len(self._datafile.variable_table.variables), 1)
        assert_equals(len(self._datafile.testcase_table.tests), 1)
        assert_equals(len(self._nth_uk(1).steps), 1)

    def _nth_uk(self, index):
        return self._datafile.keyword_table.keywords[index-1]


class TestPopulatingComments(_PopulatorTest):

    def setUp(self):
        self._datafile = TestCaseFile()
        self._populator = FromFilePopulator(self._datafile)

    def test_setting_table(self):
        self._create_table('settings', [['Force Tags', 'Foo', 'Bar', '#comment'],
                                        ['Library', 'Foo', '#Lib comment'],
                                        ['#comment', 'between rows', 'in many cells'],
                                        ['Default Tags', 'Quux', '#also end of line'],
                                        ['Variables', 'varz.py'],
                                        ['# between values'],
                                        ['...', 'arg'],
                                        ['Meta: metaname', 'metavalue'],
                                        ['#last line is commented'],
                                        ])
        self._assert_setting('force_tags', ['Foo', 'Bar'], 'comment')
        self._assert_import(0, 'Foo', [], 'Lib comment')
        self._assert_setting('default_tags', ['Quux'], 'comment | between rows | in many cells\nalso end of line')
        self._assert_import(1, 'varz.py', ['arg'], ' between values')
        self._assert_meta(0, 'metaname', 'metavalue', 'last line is commented')

    def test_variable_table(self):
        self._create_table('variables', [['${varname}', 'varvalue', '#has comment'],
                                         ['#label', 'A', 'B', 'C'],
                                         ['@{items}', '1', '2', '3'],
                                         ['${ohtervarname}', '##end comment'],
                                         ['', '', '#comment'],
                                         ['...', 'otherval'],
                                         ['#EOT']])
        self._assert_variable(0, '${varname}', ['varvalue'], 'has comment')
        self._assert_variable(1, '@{items}', ['1', '2', '3'], 'label | A | B | C')
        self._assert_variable(2, '${ohtervarname}', ['otherval'], '#end comment\ncomment\nEOT')

    def test_test_case_table(self):
        self._create_table('test cases', [['#start of table comment'],
                                          ['Test case'],
                                          ['', 'No operation', '#step comment'],
                                          ['', '', '#This step has only comment'],
                                          ['Another test', '#comment in name row'],
                                          ['', 'Log many', 'argh'],
                                          ['#', 'Comment between step def'],
                                          ['', '...', 'urgh'],
                                          ['Test with for loop'],
                                          ['',':FOR', 'v*ttuperkele'],
                                          ['#commented out in for loop'],
                                          ['','', 'Fooness in the bar', '#end commtne'],
                                          ['','#', 'Barness'],
                                          ['', 'Lodi']
                                          ])
        assert_equals(self._first_test().steps[0].comment, 'start of table comment')
        assert_equals(self._first_test().steps[1].comment, 'step comment')
        assert_equals(self._first_test().steps[2].comment, 'This step has only comment')
        assert_equals(self._nth_test(2).steps[0].comment, 'comment in name row')
        assert_equals(self._nth_test(2).steps[1].comment, ' | Comment between step def')
        assert_equals(self._nth_test(2).steps[1].args, ['argh', 'urgh'])
        assert_equals(self._nth_test(3).steps[0].steps[0].comment, 'commented out in for loop')
        assert_equals(self._nth_test(3).steps[0].steps[1].comment, 'end commtne')
        assert_equals(self._nth_test(3).steps[1].comment, ' | Barness')
        self._number_of_steps_should_be(self._nth_test(3), 3)


class DataRowTest(unittest.TestCase):

    def test_commented_row(self):
        assert_true(DataRow(['#start of table comment']).is_commented())

    def test_escaping_empty_cells(self):
        assert_equals(DataRow(['foo', '\\', '']).all, ['foo', ''])


if __name__ == '__main__':
    unittest.main()
