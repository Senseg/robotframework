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

from __future__ import with_statement
import getopt     # optparse was not supported by Jython 2.2
import os
import re
import sys
import glob
import string
import codecs
import textwrap

from robot.errors import DataError, Information, FrameworkError
from robot.version import get_full_version

from misc import plural_or_not
from encoding import decode_output, decode_from_system, utf8open


ESCAPES = dict(
    space   = ' ', apos    = "'", quot   = '"', lt     = '<', gt     = '>',
    pipe    = '|', star    = '*', comma  = ',', slash  = '/', semic  = ';',
    colon   = ':', quest   = '?', hash   = '#', amp    = '&', dollar = '$',
    percent = '%', at      = '@', exclam = '!', paren1 = '(', paren2 = ')',
    square1 = '[', square2 = ']', curly1 = '{', curly2 = '}', bslash = '\\'
)


class ArgumentParser:
    _opt_line_re = re.compile('''
    ^\s{1,4}      # 1-4 spaces in the beginning of the line
    ((-\S\s)*)    # all possible short options incl. spaces (group 1)
    --(\S{2,})    # required long option (group 3)
    (\s\S+)?      # optional value (group 4)
    (\s\*)?       # optional '*' telling option allowed multiple times (group 5)
    ''', re.VERBOSE)

    def __init__(self, usage, name=None, version=None, arg_limits=None,
                 validator=None, auto_help=True, auto_version=True,
                 auto_escape=True, auto_pythonpath=True, auto_argumentfile=True):
        """Available options and tool name are read from the usage.

        Tool name is got from the first row of the usage. It is either the
        whole row or anything before first ' -- '.
        """
        if not usage:
            raise FrameworkError('Usage cannot be empty')
        self.name = name or usage.splitlines()[0].split(' -- ')[0].strip()
        self.version = version or get_full_version()
        self._usage = usage
        self._arg_limit_validator = ArgLimitValidator(arg_limits)
        self._validator = validator
        self._auto_help = auto_help
        self._auto_version = auto_version
        self._auto_escape = auto_escape
        self._auto_pythonpath = auto_pythonpath
        self._auto_argumentfile = auto_argumentfile
        self._short_opts = ''
        self._long_opts = []
        self._multi_opts = []
        self._toggle_opts = []
        self._names = []
        self._short_to_long = {}
        self._expected_args = ()
        self._create_options(usage)

    def parse_args(self, args_list):
        """Parse given arguments and return options and positional arguments.

        Arguments must be given as a list and are typically sys.argv[1:].

        Options are retuned as a dictionary where long options are keys. Value
        is a string for those options that can be given only one time (if they
        are given multiple times the last value is used) or None if the option
        is not used at all. Value for options that can be given multiple times
        (denoted with '*' in the usage) is a list which contains all the given
        values and is empty if options are not used. Options not taken
        arguments have value False when they are not set and True otherwise.

        Positional arguments are returned as a list in the order they are given.

        If 'check_args' is True, this method will automatically check that
        correct number of arguments, as parsed from the usage line, are given.
        If the last argument in the usage line ends with the character 's',
        the maximum number of arguments is infinite.

        Possible errors in processing arguments are reported using DataError.

        Some options have a special meaning and are handled automatically
        if defined in the usage and given from the command line:

        --escape option can be used to automatically unescape problematic
        characters given in an escaped format.

        --argumentfile can be used to automatically read arguments from
        a specified file. When --argumentfile is used, the parser always
        allows using it multiple times. Adding '*' to denote that is thus
        recommend. A special value 'stdin' can be used to read arguments from
        stdin instead of a file.

        --pythonpath can be used to add extra path(s) to sys.path.

        --help and --version automatically generate help and version messages.
        Version is generated based on the tool name and version -- see __init__
        for information how to set them. Help contains the whole usage given to
        __init__. Possible <VERSION> text in the usage is replaced with the
        given version. Possible <--ESCAPES--> is replaced with available
        escapes so that they are wrapped to multiple lines but take the same
        amount of horizontal space as <---ESCAPES--->. Both help and version
        are wrapped to Information exception.
        """
        args_list = [decode_from_system(a) for a in args_list]
        if self._auto_argumentfile:
            args_list = self._process_possible_argfile(args_list)
        opts, args = self._parse_args(args_list)
        opts, args = self._handle_special_options(opts, args)
        self._arg_limit_validator(args)
        if self._validator:
            opts, args = self._validator(opts, args)
        return opts, args

    def _handle_special_options(self, opts, args):
        if self._auto_escape and opts.get('escape'):
            opts, args = self._unescape_opts_and_args(opts, args)
        if self._auto_help and opts.get('help'):
            self._raise_help()
        if self._auto_version and opts.get('version'):
            self._raise_version()
        if self._auto_pythonpath and opts.get('pythonpath'):
            sys.path = self._get_pythonpath(opts['pythonpath']) + sys.path
        for auto, opt in [(self._auto_help, 'help'),
                          (self._auto_version, 'version'),
                          (self._auto_escape, 'escape'),
                          (self._auto_pythonpath, 'pythonpath'),
                          (self._auto_argumentfile, 'argumentfile')]:
            if auto and opt in opts:
                opts.pop(opt)
        return opts, args

    def _parse_args(self, args):
        args = [self._lowercase_long_option(a) for a in args]
        try:
            opts, args = getopt.getopt(args, self._short_opts, self._long_opts)
        except getopt.GetoptError, err:
            raise DataError(err.msg)
        return self._process_opts(opts), self._glob_args(args)

    def _lowercase_long_option(self, opt):
        if not opt.startswith('--'):
            return opt
        if '=' not in opt:
            return opt.lower()
        opt, value = opt.split('=', 1)
        return '%s=%s' % (opt.lower(), value)

    def _unescape_opts_and_args(self, opts, args):
        try:
            escape_strings = opts['escape']
        except KeyError:
            raise FrameworkError("No 'escape' in options")
        escapes = self._get_escapes(escape_strings)
        for name, value in opts.items():
            if name != 'escape':
                opts[name] = self._unescape(value, escapes)
        return opts, [self._unescape(arg, escapes) for arg in args]

    def _process_possible_argfile(self, args):
        argfile_opts = ['--argumentfile']
        for sopt, lopt in self._short_to_long.items():
            if lopt == 'argumentfile':
                argfile_opts.append('-'+sopt)
        while True:
            try:
                index = self._get_argfile_index(args, argfile_opts)
                path = args[index+1]
            except IndexError:
                break
            args[index:index+2] = self._get_args_from_file(path)
        return args

    def _get_argfile_index(self, args, argfile_opts):
        for opt in argfile_opts:
            if opt in args:
                return args.index(opt)
        raise IndexError

    def _get_args_from_file(self, path):
        if path.upper() != 'STDIN':
            content = self._read_argfile(path)
        else:
            content = decode_output(sys.__stdin__.read())
        return self._process_argfile(content)

    def _read_argfile(self, path):
        try:
            with utf8open(path) as f:
                content = f.read()
        except (IOError, UnicodeError), err:
            raise DataError("Opening argument file '%s' failed: %s"
                            % (path, err))
        if content.startswith(codecs.BOM_UTF8.decode('UTF-8')):
            content = content[1:]
        return content

    def _process_argfile(self, content):
        args = []
        for line in content.splitlines():
            line = line.strip()
            if line.startswith('-'):
                args.extend(line.split(' ', 1))
            elif line and not line.startswith('#'):
                args.append(line)
        return args

    def _get_escapes(self, escape_strings):
        escapes = {}
        for estr in escape_strings:
            try:
                name, value = estr.split(':', 1)
            except ValueError:
                raise DataError("Invalid escape string syntax '%s'. "
                                "Expected: what:with" % estr)
            try:
                escapes[value] = ESCAPES[name.lower()]
            except KeyError:
                raise DataError("Invalid escape '%s'. Available: %s"
                                % (name, self._get_available_escapes()))
        return escapes

    def _unescape(self, value, escapes):
        if value in [None, True, False]:
            return value
        if isinstance(value, list):
            return [self._unescape(item, escapes) for item in value]
        for esc_name, esc_value in escapes.items():
            if esc_name in value:
                value = value.replace(esc_name, esc_value)
        return value

    def _process_opts(self, opt_tuple):
        opts = self._init_opts()
        for name, value in opt_tuple:
            name = self._get_name(name)
            if name in self._multi_opts:
                opts[name].append(value)
            elif name in self._toggle_opts:
                opts[name] = not opts[name]
            else:
                opts[name] = value
        return opts

    def _glob_args(self, args):
        temp = []
        for path in args:
            paths = sorted(glob.glob(path))
            if paths:
                temp.extend(paths)
            else:
                temp.append(path)
        return temp

    def _init_opts(self):
        opts = {}
        for name in self._names:
            if name in self._multi_opts:
                opts[name] = []
            elif name in self._toggle_opts:
                opts[name] = False
            else:
                opts[name] = None
        return opts

    def _get_name(self, name):
        name = name.lstrip('-')
        try:
            return self._short_to_long[name]
        except KeyError:
            return name

    def _create_options(self, usage):
        for line in usage.splitlines():
            res = self._opt_line_re.match(line)
            if res:
                self._create_option(short_opts=[o[1] for o in res.group(1).split()],
                                    long_opt=res.group(3).lower(),
                                    takes_arg=bool(res.group(4)),
                                    is_multi=bool(res.group(5)))

    def _create_option(self, short_opts, long_opt, takes_arg, is_multi):
        if long_opt in self._names:
            self._raise_option_multiple_times_in_usage('--' + long_opt)
        self._names.append(long_opt)
        for sopt in short_opts:
            if self._short_to_long.has_key(sopt):
                self._raise_option_multiple_times_in_usage('-' + sopt)
            self._short_to_long[sopt] = long_opt
        if is_multi:
            self._multi_opts.append(long_opt)
        if takes_arg:
            long_opt += '='
            short_opts = [sopt+':' for sopt in short_opts]
        else:
            self._toggle_opts.append(long_opt)
        self._long_opts.append(long_opt)
        self._short_opts += (''.join(short_opts))

    def _get_pythonpath(self, paths):
        if isinstance(paths, basestring):
            paths = [paths]
        temp = []
        for path in self._split_pythonpath(paths):
            temp.extend(glob.glob(path))
        return [os.path.abspath(path) for path in temp if path]

    def _split_pythonpath(self, paths):
        # paths may already contain ':' as separator
        tokens = ':'.join(paths).split(':')
        if os.sep == '/':
            return tokens
        # Fix paths split like 'c:\temp' -> 'c', '\temp'
        ret = []
        drive = ''
        for item in tokens:
            item = item.replace('/', '\\')
            if drive and item.startswith('\\'):
                ret.append('%s:%s' % (drive, item))
                drive = ''
                continue
            if drive:
                ret.append(drive)
                drive = ''
            if len(item) == 1 and item in string.letters:
                drive = item
            else:
                ret.append(item)
        if drive:
            ret.append(drive)
        return ret

    def _get_available_escapes(self):
        names = sorted(ESCAPES.keys(), key=str.lower)
        return ', '.join('%s (%s)' % (n, ESCAPES[n]) for n in names)

    def _raise_help(self):
        msg = self._usage
        if self.version:
            msg = msg.replace('<VERSION>', self.version)
        def replace_escapes(res):
            escapes = 'Available escapes: ' + self._get_available_escapes()
            lines = textwrap.wrap(escapes, width=len(res.group(2)))
            indent = ' ' * len(res.group(1))
            return '\n'.join(indent + line for line in lines)
        msg = re.sub('( *)(<-+ESCAPES-+>)', replace_escapes, msg)
        raise Information(msg)

    def _raise_version(self):
        raise Information('%s %s' % (self.name, self.version))

    def _raise_option_multiple_times_in_usage(self, opt):
        raise FrameworkError("Option '%s' multiple times in usage" % opt)


class ArgLimitValidator(object):

    def __init__(self, arg_limits):
        self._min_args, self._max_args = self._parse_arg_limits(arg_limits)

    def _parse_arg_limits(self, arg_limits):
        if arg_limits is None:
            return 0, sys.maxint
        if isinstance(arg_limits, int):
            return arg_limits, arg_limits
        if len(arg_limits) == 1:
            return arg_limits[0], sys.maxint
        return arg_limits[0], arg_limits[1]

    def __call__(self, args):
        if not (self._min_args <= len(args) <= self._max_args):
            self._raise_invalid_args(self._min_args, self._max_args, len(args))

    def _raise_invalid_args(self, min_args, max_args, arg_count):
        min_end = plural_or_not(min_args)
        if min_args == max_args:
            expectation = "%d argument%s" % (min_args, min_end)
        elif max_args != sys.maxint:
            expectation = "%d to %d arguments" % (min_args, max_args)
        else:
            expectation = "at least %d argument%s" % (min_args, min_end)
        raise DataError("Expected %s, got %d." % (expectation, arg_count))
