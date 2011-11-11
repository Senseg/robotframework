#  Copyright 2008-2011 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from robot import model, utils

from keyword import Keyword


class TestCase(model.TestCase):
    __slots__ = ['status', 'message', 'starttime', 'endtime']
    keyword_class = Keyword

    def __init__(self, name='', doc='', tags=None, timeout='', status='FAIL',
                 message='', starttime='N/A', endtime='N/A'):
        model.TestCase.__init__(self, name, doc, tags, timeout)
        self.status = status
        self.message = message
        self.starttime = starttime
        self.endtime = endtime

    @property
    def elapsedtime(self):
        return utils.get_elapsed_time(self.starttime, self.endtime)

    # TODO: Rename to passed
    @property
    def is_passed(self):
        return self.status == 'PASS'
