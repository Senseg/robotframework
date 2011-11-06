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

from robot import utils


class _NamePatterns(object):

    def __init__(self, patterns=None):
        self._matchers = [utils.Matcher(p, ignore=['_'])
                          for p in self._ensure_list(patterns)]

    def _ensure_list(self, patterns):
        if patterns is None:
            return []
        if isinstance(patterns, basestring):
            return  [patterns]
        return patterns

    def match(self, name, longname=None):
        return self._match(name) or longname and self._match_longname(longname)

    def _match(self, name):
        return any(matcher.match(name) for matcher in self._matchers)

    def __nonzero__(self):
        return bool(self._matchers)


class SuiteNamePatterns(_NamePatterns):

    def _match_longname(self, name):
        while '.' in name:
            if self._match(name):
                return True
            name = name.split('.', 1)[1]
        return False


class TestNamePatterns(_NamePatterns):

    def _match_longname(self, name):
        return self._match(name)
