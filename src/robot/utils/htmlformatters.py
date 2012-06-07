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

import re
from functools import partial
from itertools import cycle


class LinkFormatter(object):
    _image_exts = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    _link = re.compile('\[(.+?\|.*?)\]')
    _url = re.compile('''
((^|\ ) ["'([]*)           # begin of line or space and opt. any char "'([
(\w{3,9}://[\S]+?)         # url (protocol is any alphanum 3-9 long string)
(?=[])"'.,!?:;]* ($|\ ))   # opt. any char ])"'.,!?:; and end of line or space
''', re.VERBOSE|re.MULTILINE)

    def format_url(self, text):
        return self._format_url(text, format_as_image=False)

    def _format_url(self, text, format_as_image=True):
        if '://' not in text:
            return text
        return self._url.sub(partial(self._replace_url, format_as_image), text)

    def _replace_url(self, format_as_image, match):
        pre = match.group(1)
        url = match.group(3)
        if format_as_image and self._is_image(url):
            return pre + self._get_image(url)
        return pre + self._get_link(url)

    def _get_image(self, src, title=None):
        return '<img src="%s" title="%s">' \
                % (self._quot(src), self._quot(title or src))

    def _get_link(self, href, content=None):
        return '<a href="%s">%s</a>' % (self._quot(href), content or href)

    def _quot(self, attr):
        return attr if '"' not in attr else attr.replace('"', '&quot;')

    def format_link(self, text):
        # 2nd, 4th, etc. token contains link, others surrounding content
        tokens = self._link.split(text)
        formatters = cycle((self._format_url, self._format_link))
        return ''.join(f(t) for f, t in zip(formatters, tokens))

    def _format_link(self, text):
        link, content = [t.strip() for t in text.split('|', 1)]
        if self._is_image(content):
            content = self._get_image(content, link)
        elif self._is_image(link):
            return self._get_image(link, content)
        return self._get_link(link, content)

    def _is_image(self, text):
        return text.lower().endswith(self._image_exts)


class LineFormatter(object):
    handles = lambda self, line: True
    newline = '\n'
    _bold = re.compile('''
(                         # prefix (group 1)
  (^|\ )                  # begin of line or space
  ["'(]* _?               # optionally any char "'( and optional begin of italic
)                         #
\*                        # start of bold
([^\ ].*?)                # no space and then anything (group 3)
\*                        # end of bold
(?=                       # start of postfix (non-capturing group)
  _? ["').,!?:;]*         # optional end of italic and any char "').,!?:;
  ($|\ )                  # end of line or space
)
''', re.VERBOSE)
    _italic = re.compile('''
( (^|\ ) ["'(]* )          # begin of line or space and opt. any char "'(
_                          # start of italic
([^\ _].*?)                # no space or underline and then anything
_                          # end of italic
(?= ["').,!?:;]* ($|\ ) )  # opt. any char "').,!?:; and end of line or space
''', re.VERBOSE)

    def __init__(self):
        self._format_link = LinkFormatter().format_link

    def format(self, line):
        return self._format_link(self._format_italic(self._format_bold(line)))

    def _format_bold(self, line):
        return self._bold.sub('\\1<b>\\3</b>', line) if '*' in line else line

    def _format_italic(self, line):
        return self._italic.sub('\\1<i>\\3</i>', line) if '_' in line else line


class HtmlFormatter(object):

    def __init__(self):
        self._results = []
        self._formatters = [TableFormatter(),
                            PreformattedFormatter(),
                            ListFormatter(),
                            RulerFormatter()]
        self._formatters.append(ParagraphFormatter(self._formatters[:]))
        self._current = None

    def format(self, text):
        for line in text.splitlines():
            self._process_line(line.strip())
        self._end_current()
        return '\n'.join(self._results)

    def _process_line(self, line):
        if not line:
            self._end_current()
        elif self._current and self._current.handles(line):
            self._current.add(line)
        else:
            self._end_current()
            self._current = self._find_formatter(line)
            self._current.add(line)

    def _end_current(self):
        if self._current:
            self._results.append(self._current.end())
            self._current = None

    def _find_formatter(self, line):
        for formatter in self._formatters:
            if formatter.handles(line):
                return formatter


class _BlockFormatter(object):

    def __init__(self):
        self._lines = []

    def add(self, line):
        self._lines.append(line)

    def end(self):
        result = self.format(self._lines)
        self._lines = []
        return result

    def format(self, lines):
        raise NotImplementedError


class RulerFormatter(_BlockFormatter):
    _hr_matcher = re.compile('^-{3,}$').match

    def handles(self, line):
        return not self._lines and self._hr_matcher(line)

    def format(self, lines):
        return '<hr>'


class ParagraphFormatter(_BlockFormatter):
    _format_line = LineFormatter().format

    def __init__(self, other_formatters):
        _BlockFormatter.__init__(self)
        self._other_formatters = other_formatters

    def handles(self, line):
        if any(formatter.handles(line) for formatter in self._other_formatters):
            return False
        if line:
            return True
        return not self._lines

    def format(self, lines):
        return '<p>%s</p>' % self._format_line(' '.join(lines))


class TableFormatter(_BlockFormatter):
    handles = re.compile('^\| (.* |)\|$').match
    _line_splitter = re.compile(' \|(?= )')
    _format_cell = LineFormatter().format

    def format(self, lines):
        return self._format_table([self._split_to_cells(l) for l in lines])

    def _split_to_cells(self, line):
        return [cell.strip() for cell in self._line_splitter.split(line[1:-1])]

    def _format_table(self, rows):
        maxlen = max(len(row) for row in rows)
        table = ['<table>']
        for row in rows:
            row += [''] * (maxlen - len(row))  # fix ragged tables
            table.append('<tr>')
            table.extend('<td>%s</td>' % self._format_cell(c) for c in row)
            table.append('</tr>')
        table.append('</table>')
        return '\n'.join(table)


class PreformattedFormatter(_BlockFormatter):
    _format_line = LineFormatter().format

    def handles(self, line):
        return line.startswith('| ') or line == '|'

    def format(self, lines):
        lines = [self._format_line(line[2:]) for line in lines]
        return '\n'.join(['<pre>'] + lines + ['</pre>'])


class ListFormatter(_BlockFormatter):
    _format_item = LineFormatter().format

    def handles(self, line):
        return line.startswith('- ')

    def format(self, lines):
        items = ['<li>%s</li>' % self._format_item(line[2:].strip())
                 for line in lines]
        return '\n'.join(['<ul>'] + items + ['</ul>'])
