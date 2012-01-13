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

import os
import sys
from java.lang import String


# Global workaround for os.listdir bug http://bugs.jython.org/issue1593
# This bug has been fixed in Jython 2.5.2.
if sys.version_info[:3] < (2, 5, 2):
    os._orig_listdir = os.listdir
    def listdir(path):
        items = os._orig_listdir(path)
        if isinstance(path, unicode):
            items = [unicode(String(i).toString()) for i in items]
        return items
    os.listdir = listdir


# Global workaround for os.stat bug on Windows http://bugs.jython.org/issue1658
# The bug still exists in Jython 2.5.2 but the workaround doesn't work anymore.
if os.sep == '\\' and sys.version_info[:3] < (2, 5, 2):
    os._posix = os.JavaPOSIX(os.PythonPOSIXHandler())
    os._native_posix = False

