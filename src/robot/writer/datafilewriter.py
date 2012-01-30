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

from robot.errors import DataError
from .filewriters import FileWriter


class DataFileWriter(object):
    """Writes parsed Robot Framework test data file objects back to disk."""

    def __init__(self, **options):
        """:param options: used to create a :py:class:`.WriteConfiguration`."""
        self._options = options

    def write(self, datafile):
        """Writes given `datafile` using `**options`.

        :param datafile: A robot.parsing.model.DataFile object to be written
        """
        with WritingContext(datafile, **self._options) as ctx:
            FileWriter(ctx).write(datafile)


class WritingContext(object):
    """Contains configuration used in writing a test data file to disk."""
    encoding = 'UTF-8'
    txt_format = 'txt'
    html_format = 'html'
    tsv_format = 'tsv'
    txt_column_count = 8
    html_column_count = 5
    tsv_column_count = 8
    _formats = [txt_format, html_format, tsv_format]

    def __init__(self, datafile, format='', output=None,
                 pipe_separated=False, line_separator=os.linesep):
        """
        :param datafile: The datafile to be written.
        :type datafile: :py:class:`~robot.parsing.model.TestCaseFile`,
            :py:class:`~robot.parsing.model.ResourceFile`,
            :py:class:`~robot.parsing.model.TestDataDirectory`
        :param str format: Output file format. If omitted, read from the
            extension of the `source` attribute of the given `datafile`.
        :param output: An open, file-like object used in writing. If
            omitted, value of `source` attribute of the given `datafile` is
            used to construct a new file object.
        :param bool pipe_separated: Whether to use pipes as separator when
            output file format is txt.
        :param str line_separator: Line separator used in output files.

        If `output` is not given, an output file is created based on the source
        of the given datafile and value of `format`. Examples:

            WriteConfiguration(datafile, output=StringIO) ->
               Output written in the StringIO instance using format of
              `datafile.source`
            WriteConfiguration(datafile, format='html') ->
               Output file is created from `datafile.source` by stripping
               extension and replacing it with `html`.
        """
        self.datafile = datafile
        self.pipe_separated = pipe_separated
        self.line_separator = line_separator
        self._given_output = output
        self.format = self._validate_format(format) or self._format_from_file()
        self.output = output

    def __enter__(self):
        if not self.output:
            self.output = open(self._output_path(), 'wb')
        return self

    def __exit__(self, *exc_info):
        if self._given_output is None:
            self.output.close()

    def _validate_format(self, format):
        format = format.lower() if format else ''
        if format and format not in self._formats:
            raise DataError('Invalid format: %s' % format)
        return format

    def _format_from_file(self):
        return self._format_from_extension(self._source_from_file())

    def _format_from_extension(self, path):
        return os.path.splitext(path)[1][1:].lower()

    def _output_path(self):
        return '%s.%s' % (self._base_name(), self.format)

    def _base_name(self):
        return os.path.splitext(self._source_from_file())[0]

    def _source_from_file(self):
        return getattr(self.datafile, 'initfile', self.datafile.source)
