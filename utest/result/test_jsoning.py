import unittest
from robot import utils
from robot.result.keyword import Keyword
from robot.model.message import Message
from robot.output.loggerhelper import LEVELS
from robot.reporting.parsingcontext import Context
from robot.result.datamodel import DatamodelVisitor
from robot.result.jsondatamodelhandlers import _Handler, KeywordHandler, _StatusHandler
from robot.utils.asserts import assert_equals


class TestJsoning(unittest.TestCase, DatamodelVisitor):

    def setUp(self):
        self._elements = []
        self._context = Context()
        self._elements.append(_Handler(self._context))

    def test_html_message_to_json(self):
        message = Message(message='<b>Great danger!</b>',
                          level='WARN',
                          html=True,
                          timestamp='20121212 12:12:12.121')
        message.visit(self)
        self._verify_message(self.datamodel[0], message)

    def _verify_message(self, message_json, message):
        assert_equals(message_json[0], self._context.timestamp(message.timestamp))
        assert_equals(message_json[1], LEVELS[message.level])
        message_text = message.message
        if not message.html:
            message_text = utils.html_escape(message_text)
        self._assert_text(message_json[2], message_text)

    def _assert_text(self, text_index, text):
        assert_equals(text_index, self._context.get_id(text))

    def test_non_html_message_to_json(self):
        message = Message(message='This is an html mark --> <html>',
                          level='INFO',
                          timestamp='19991211 12:12:12.821')
        message.visit(self)
        self._verify_message(self.datamodel[0], message)

    def test_times(self):
        for timestamp in ['20110531 12:48:09.020','N/A','20110531 12:48:09.010','20110531 12:48:19.035']:
            Message(timestamp=timestamp).visit(self)
        for index, millis in enumerate([0, None, -10, 10015]):
            assert_equals(self.datamodel[index][0], millis)

    def test_keyword_jsoning(self):
        self._context.start_suite()
        keyword = Keyword(name='Keyword Name',
                          doc='Documentation for <b>a keyword</b>',
                          args=['${first}', '${second}', '${third}'],
                          type='setup',
                          timeout='2 seconds',
                          status='PASS',
                          starttime='20110101 16:16:16.100',
                          endtime='20110101 16:16:18.161')
        keyword.messages.create(message='keyword message',
                                level='INFO',
                                timestamp='20110101 16:16:16.161')
        keyword.keywords.create(name='No Operation',
                                type='kw',
                                status='PASS')
        keyword.visit(self)
        self._verify_keyword(self.datamodel[0], keyword)

    def _verify_keyword(self, keyword_json, keyword):
        assert_equals(keyword_json[0], KeywordHandler._types[keyword.type])
        self._assert_text(keyword_json[1], keyword.name)
        self._assert_text(keyword_json[2], keyword.timeout)
        self._assert_html_text(keyword_json[3], keyword.doc)
        self._assert_text(keyword_json[4], ', '.join(keyword.args))
        assert_equals(keyword_json[-3][0], _StatusHandler._statuses[keyword.status])
        assert_equals(keyword_json[-3][1], self._millis(keyword.starttime))
        if keyword.starttime != 'N/A':
            assert_equals(keyword_json[-3][2], self._millis(keyword.endtime)-self._millis(keyword.starttime))
        for index, message in enumerate(keyword.messages):
            self._verify_message(keyword_json[-1][index], message)
        for index, kw in enumerate(keyword.keywords):
            self._verify_keyword(keyword_json[-2][index], kw)

    def _millis(self, timestamp):
        return self._context.timestamp(timestamp)

    def _assert_html_text(self, text_index, text):
        self._assert_text(text_index, utils.html_escape(text))


if __name__ == '__main__':
    unittest.main()
