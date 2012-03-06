#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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

from robot.model import ItemList
from robot.utils import setter

from .message import Message


class ExecutionErrors(object):
    message_class = Message

    def __init__(self, messages=None):
        self.messages = messages

    @setter
    def messages(self, msgs):
        return ItemList(self.message_class, items=msgs)

    def add(self, other):
        self.messages.extend(other.messages)

    def visit(self, visitor):
        visitor.visit_errors(self)

    def __iter__(self):
        return iter(self.messages)

    def __len__(self):
        return len(self.messages)
