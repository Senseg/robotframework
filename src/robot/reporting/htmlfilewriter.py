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

from __future__ import with_statement
import os
import re

from robot.utils import HtmlWriter
from robot.version import get_full_version

from .jswriter import JsResultWriter
from .webcontentfile import WebContentFile


class HtmlFileWriter(object):

    def __init__(self, output, model, config):
        html_writer = HtmlWriter(output)
        self._writers = (ModelWriter(output, model, config),
                         JsFileWriter(html_writer),
                         CssFileWriter(html_writer),
                         GeneratorWriter(html_writer),
                         LineWriter(output))

    def write(self, template):
        for line in WebContentFile(template):
            for writer in self._writers:
                if writer.handles(line):
                    writer.write(line)
                    break


class _Writer(object):
    _handles_line = None

    def handles(self, line):
        return line.startswith(self._handles_line)

    def write(self, line):
        raise NotImplementedError


class ModelWriter(_Writer):
    _handles_line = '<!-- JS MODEL -->'

    def __init__(self, output, model, config):
        self._output = output
        self._model = model
        self._config = config

    def write(self, line):
        JsResultWriter(self._output).write(self._model, self._config)


class LineWriter(_Writer):

    def __init__(self, output):
        self._output = output

    def handles(self, line):
        return True

    def write(self, line):
        self._output.write(line + os.linesep)


class GeneratorWriter(_Writer):
    _handles_line = '<meta name="Generator" content='

    def __init__(self, html_writer):
        self._html_writer = html_writer

    def write(self, line):
        version = get_full_version('Robot Framework')
        self._html_writer.start('meta', {'name': 'Generator', 'content': version})


class _InliningWriter(_Writer):

    def __init__(self, html_writer):
        self._html_writer = html_writer

    def _inline_file(self, filename, tag, attrs):
        self._html_writer.start(tag, attrs)
        for line in WebContentFile(filename):
            self._html_writer.content(line + os.linesep, escape=False)
        self._html_writer.end(tag)


class JsFileWriter(_InliningWriter):
    _handles_line = '<script type="text/javascript" src='
    _source_file = re.compile('src=\"([^\"]+)\"')

    def write(self, line):
        name = self._source_file.search(line).group(1)
        self._inline_file(name, 'script', {'type': 'text/javascript'})


class CssFileWriter(_InliningWriter):
    _handles_line = '<link rel="stylesheet"'
    _source_file = re.compile('href=\"([^\"]+)\"')
    _media_type = re.compile('media=\"([^\"]+)\"')

    def write(self, line):
        name = self._source_file.search(line).group(1)
        media = self._media_type.search(line).group(1)
        self._inline_file(name, 'style', {'type': 'text/css', 'media': media})
