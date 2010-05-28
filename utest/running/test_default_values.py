import unittest

from robot.utils.asserts import *
from robot.running.defaultvalues import DefaultValues
from robot.parsing.model import TestCaseFileSettingTable, InitFileSettingTable
from robot.parsing.settings import Tags, Fixture, Template


class TestDefaultValues(unittest.TestCase):

    def setUp(self):
        dir_table = InitFileSettingTable(None)
        dir_table.force_tags.set(['dir_force_tag1','dir_force_tag2'])
        dir_table.test_setup.set(['dir_setup','arg'], 'comment')
        directory = DefaultValues(dir_table)
        tcf_table = TestCaseFileSettingTable(None)
        tcf_table.force_tags.set(['tcf_force_tag1','tcf_force_tag2'])
        tcf_table.default_tags.set(['tcf_default_tag1','tcf_default_tag2'])
        tcf_table.test_template.set(['Foo'])
        self.tcf_defaults = DefaultValues(tcf_table, directory)

    def test_default_tags(self):
        tc_tags = Tags()
        assert_equal(self.tcf_defaults.get_tags(tc_tags), 
                     ['tcf_default_tag1','tcf_default_tag2','tcf_force_tag1',
                      'tcf_force_tag2','dir_force_tag1','dir_force_tag2'])

    def test_overriding_default_tags(self):
        tc_tags = Tags()
        tc_tags.set(['test_tag1','test_tag2'])
        assert_equal(self.tcf_defaults.get_tags(tc_tags), 
                     ['test_tag1','test_tag2','tcf_force_tag1',
                      'tcf_force_tag2','dir_force_tag1','dir_force_tag2'])

    def test_setup_from_directory(self):
        setup = self.tcf_defaults.get_setup(Fixture())
        assert_equal(setup.name,'dir_setup')
        assert_equal(setup.args,['arg'])

    def test_teardown_empty(self):
        assert_equal(self.tcf_defaults.get_teardown(Fixture()).name,'')

    def test_teardown_from_test(self):
        teardown = Fixture()
        teardown.set(['name','arg','arg2'])
        assert_equal(self.tcf_defaults.get_teardown(teardown).name,'name')

    def test_template(self):
        template = Template()
        assert_equal(self.tcf_defaults.get_template(template),'Foo')
        template.set(['Bar'])
        assert_equal(self.tcf_defaults.get_template(template),'Bar')


if __name__ == "__main__":
    unittest.main()