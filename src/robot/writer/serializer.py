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
import codecs

from .writer import FileWriter


class Serializer(object):
    """The Serializer object. It is used to serialize Robot Framework test
    data files.
    """

    def serialize(self, datafile, **options):
        """Serializes given `datafile` using `**options`.

        :param datafile: A robot.parsing.model.DataFile object to be serialized
        :param options: A :py:class:`.SerializationContext` is initialized based on these
        """
        context = SerializationContext(datafile, **options)
        FileWriter(context).write(datafile)
        context.finish()


class SerializationContext(object):
    """The SerializationContext object. It holds needed information for
    serializing a test data file.
    """

    def __init__(self, datafile, path=None, format=None, output=None,
                 recursive=False, pipe_separated=False,
                 line_separator=os.linesep):
        """
        :param datafile: The datafile to be serialized.
        :type datafile: :py:class:`~robot.parsing.model.TestCaseFile`,
            :py:class:`~robot.parsing.model.ResourceFile`,
            :py:class:`~robot.parsing.model.TestDataDirectory`
        :param str path: Output file name. If omitted, basename of the `source`
            attribute of the given `datafile` is used. If `path` contains
            extension, it overrides the value of `format` option.
        :param str format: Serialization format. If omitted, read from the
            extension of the `source` attribute of the given `datafile`.
        :param output: An open, file-like object used in serialization. If
            omitted, value of `source` attribute of the given `datafile` is
            used to construct a new file object.
        :param bool pipe_separated: Whether to use pipes as separator when
            serialization format is txt.
        :param str line_separator: Line separator used in serialization.
        """
        self.datafile = datafile
        self.recursive = recursive
        self.pipe_separated = pipe_separated
        self.line_separator = line_separator
        self._given_output = output
        self._path = path
        self._format = format
        self._output = output

    @property
    def output(self):
        if not self._output:
            self._output = codecs.open(self._get_source(), 'wb', 'UTF-8')
        return self._output

    @property
    def format(self):
        return self._format_from_path() or self._format or self._format_from_file()

    def finish(self):
        if self._given_output is None:
            self._output.close()

    def _get_source(self):
        return self._path or '%s.%s' % (self._basename(), self.format)

    def _basename(self):
        return os.path.splitext(self._source_from_file())[0]

    def _source_from_file(self):
        return getattr(self.datafile, 'initfile', self.datafile.source)

    def _format_from_path(self):
        if not self._path:
            return ''
        return self._format_from_extension(self._path)

    def _format_from_file(self):
        return self._format_from_extension(self._source_from_file())

    def _format_from_extension(self, path):
        return os.path.splitext(path)[1][1:].lower()
