#!/usr/bin/env python

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

USAGE = """robot.libdoc -- Robot Framework library documentation generator

Version:  <VERSION>

Usage:  python -m robot.libdoc [options] library output_file
   or:  python -m robot.libdoc [options] library list|show|version [names]

Libdoc tool can generate keyword documentation in HTML and XML formats both
for test libraries and resource files. HTML format is suitable for humans and
XML specs for RIDE and other tools. Libdoc also has few special commands to
show library or resource information on the console.

Libdoc supports all library and resource types and also earlier generated XML
specs can be used as input. If a library needs arguments, they must be given
as part of the library name and separated by two colons, for example, like
`LibraryName::arg1::arg2`.

Options
=======

 -f --format HTML|XML     Specifies whether to generate HTML or XML output.
                          If this options is not used, the format is got
                          from the extension of the output file.
 -n --name newname        Sets the name of the documented library or resource.
 -v --version newversion  Sets the version of the documented library or
                          resource.
 -P --pythonpath path *   Additional locations where to search for libraries
                          and resources.
 -E --escape what:with *  Escapes characters which are problematic in console.
                          'what' is the name of the character to escape and
                          'with' is the string to escape it with.
                          <-------------------ESCAPES------------------------>
 -h -? --help             Print this help.

Creating documentation
======================

When creating documentation in HTML or XML format, the output file must
be specified as a second argument after the library/resource name or path.
Output format is got automatically from the extension but can also be set
with `--format` option.

Examples:

  python -m robot.libdoc src/MyLib.py doc/MyLib.html
  jython -m robot.libdoc MyJavaLibrary.java MyJavaLibrary.html
  python -m robot.libdoc --name MyLib Remote::10.0.0.42:8270 MyLib.xml

Viewing information on console
==============================

Libdoc has three special commands to show information on the console. These
commands are used instead of the name of the output file, and they can also
take additional arguments.

list:    List names of the keywords the library/resource contains. Can be
         limited to show only certain keywords by passing optional patterns as
         arguments. Keyword is listed if its name contains any given pattern.
show:    Show library/resource documentation. Can be limited to show only
         certain keywords by passing names as arguments. Keyword is shown if
         its name matches any given name. Special argument `intro` will show
         the library introduction and importing sections.
version: Show library version

Optional patterns given to `list` and `show` are case and space insensitive.
Both also accept `*` and `?` as wildcards.

Examples:

  python -m robot.libdoc Dialogs list
  python -m robot.libdoc Selenium2Library list browser
  python -m robot.libdoc Remote::10.0.0.42:8270 show
  python -m robot.libdoc Dialogs show PauseExecution execute*
  python -m robot.libdoc Selenium2Library show intro
  python -m robot.libdoc Selenium2Library version

Alternative execution
=====================

Libdoc works with all interpreters supported by Robot Framework (Python,
Jython and IronPython). In the examples above libdoc is executed as an
installed module, but it can also be executed as a script like
`python path/robot/libdoc.py`.

For more information see libdoc section in Robot Framework User Guide at
http://code.google.com/p/robotframework/wiki/UserGuide
"""

import sys
import os

# Allows running as a script. __name__ check needed with multiprocessing:
# http://code.google.com/p/robotframework/issues/detail?id=1137
if 'robot' not in sys.modules and __name__ == '__main__':
    import pythonpathsetter

from robot.utils import Application
from robot.errors import DataError
from robot.libdocpkg import LibraryDocumentation, ConsoleViewer


class LibDoc(Application):

    def __init__(self):
        Application.__init__(self, USAGE, arg_limits=(2,), auto_version=False)

    def validate(self, options, arguments):
        if ConsoleViewer.handles(arguments[1]):
            ConsoleViewer.validate_command(arguments[1], arguments[2:])
        elif len(arguments) > 2:
            raise DataError('Only two arguments allowed when writing output.')
        return options, arguments

    def main(self, args, name='', version='', format=None):
        lib_or_res, output = args[:2]
        libdoc = LibraryDocumentation(lib_or_res, name, version)
        if ConsoleViewer.handles(output):
            ConsoleViewer(libdoc).view(output, *args[2:])
        else:
            libdoc.save(output, self._get_format(format, output))
            self.console(os.path.abspath(output))

    def _get_format(self, format, output):
        format = (format if format else os.path.splitext(output)[1][1:]).upper()
        if format in ['HTML', 'XML']:
            return format
        raise DataError("Format must be either 'HTML' or 'XML', got '%s'." % format)


def libdoc_cli(args):
    """Executes libdoc similarly as from the command line.

    :param args: command line arguments as a list of strings.

    Example:
        libdoc_cli(['--name', 'Something', 'MyLibrary.py', 'doc.html'])
    """
    LibDoc().execute_cli(args)


def libdoc(library_or_resource, outfile, name='', version='', format=None):
    """Executes libdoc.

    Arguments are same as command line options to libdoc.py.

    Example:
        libdoc('MyLibrary.py', 'MyLibrary.html', version='1.0')
    """

    LibDoc().execute(library_or_resource, outfile, name=name, version=version,
                     format=format)


if __name__ == '__main__':
    libdoc_cli(sys.argv[1:])
