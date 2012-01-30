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

import re

from .aligners import FirstColumnAligner, ColumnAligner
from .dataextractor import DataExtractor
from .rowsplitter import RowSplitter


class _DataFileFormatter(object):
    _want_names_on_first_content_row = False

    def __init__(self, column_count):
        self._splitter = RowSplitter(column_count)
        self._column_count = column_count
        self._extractor = DataExtractor(self._want_names_on_first_content_row)

    def empty_row_after(self, table):
        return self._format_row([], table)

    def format_header(self, table):
        return self._format_row(self._header_for(table))

    def format_table(self, table):
        rows = self._extractor.rows_from_table(table)
        if self._should_split_rows(table):
            return self._split_rows(rows, table)
        return [self._format_row(r, table) for r in rows]

    def _should_split_rows(self, table):
        if self._should_align_columns(table):
            return False
        return True

    def _split_rows(self, rows, table):
        for row in rows:
            for r in self._splitter.split(row, self._is_indented_table(table)):
                yield self._format_row(r, table)

    def _should_align_columns(self, table):
        return self._is_indented_table(table) and bool(table.header[1:])

    def _is_indented_table(self, table):
        return bool(table is not None and table.type in ['test case', 'keyword'])

    def _escape_consecutive_whitespace(self, row):
        return [re.sub('\s\s+(?=[^\s])',
            lambda match: '\\'.join(match.group(0)), item.replace('\n', ' ')) for item in row]

    def _format_row(self, row, table=None):
        raise NotImplementedError

    def _header_for(self, table):
        raise NotImplementedError


class TsvFormatter(_DataFileFormatter):

    def _header_for(self, table):
        return ['*%s*' % cell for cell in table.header]

    def _format_row(self, row, table=None):
        return self._pad(self._escape(row))

    def _escape(self, row):
        return self._escape_consecutive_whitespace(
            self._escape_tabs(row))

    def _escape_tabs(self, row):
        return [c.replace('\t', '\\t') for c in row]

    def _pad(self, row):
        row = [cell.replace('\n', ' ') for cell in row]
        return row + [''] * (self._column_count - len(row))


class TxtFormatter(_DataFileFormatter):
    _test_or_keyword_name_width = 18
    _setting_and_variable_name_width = 14

    def _format_row(self, row, table=None):
        row = self._escape(row)
        aligner = self._aligner_for(table)
        if aligner:
            return aligner.align_row(row)
        return row

    def _aligner_for(self, table):
        if table and table.type in ['setting', 'variable']:
            return FirstColumnAligner(self._setting_and_variable_name_width)
        if self._should_align_columns(table):
            return ColumnAligner(self._test_or_keyword_name_width, table)
        return None

    def _header_for(self, table):
        header = ['*** %s ***' % table.header[0]] + table.header[1:]
        aligner = self._aligner_for(table)
        if aligner:
            return aligner.align_row(header)
        return header

    def _escape(self, row):
        return self._escape_consecutive_whitespace(
            self._escape_empty_cell_from_start(row))

    def _escape_empty_cell_from_start(self, row):
        if len(row) >= 2 and row[0] == row[1] == '':
            row[1] = '\\'
        return row


class PipeFormatter(TxtFormatter):

    def _escape(self, row):
        row = self._format_empty_cells(row)
        return self._escape_consecutive_whitespace(self._escape_pipes(row))

    def _format_empty_cells(self, row):
        return ['  ' if not cell else cell for cell in row]

    def _escape_pipes(self, row):
        return [self._escape_pipes_from_cell(cell) for cell in row]

    def _escape_pipes_from_cell(self, cell):
        cell = cell.replace(' | ', ' \\| ')
        if cell.startswith('| '):
            cell = '\\' + cell
        if cell.endswith(' |'):
            cell = cell[:-1] + '\\|'
        return cell
