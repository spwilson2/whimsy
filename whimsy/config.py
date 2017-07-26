# TODO: Add support for using some kind of config file for testing.
import abc
import argparse
import numbers
import sys
import types
import copy
import ConfigParser
import os

import helper
import _util

class _Config(object):
    '''
    Config object that automatically parses args when one attempts to get
    a config attr.
    '''
    # sentinal object to signal an unconfigured argument format.
    _unconfigured = object()
    _cli_args = _unconfigured
    _config_file_args = _unconfigured
    _config = {}
    __shared_dict = {}
    constants = _util.AttrDict()

    def __init__(self):
        self.__dict__ = self.__shared_dict

    @helper.cacheresult
    def _parse_config_file(self):
        # First check if we have recieved a commandline argument telling us to
        # look outside of the default location for our testing.ini file.
        configpath = None
        if self._config_file_args != self._unconfigured \
                and common_args.configpath.name in self._config_file_args:
            configpath = _config_file_args[common_args.configpath.name]

        if configpath is None:
            self._config_file_args = None
        #TODO: We'll need to check if values are already set in the config
        # since we won't want to overwrite command line arguments with
        # a config file. (Command line arguments should take precedence.)


    @helper.cacheresult
    def _parse_commandline_args(self):
        args = baseparser.parse_args()
        # Finish up our verbose args incrementing hack.
        args.verbose = args.verbose.val
        self._config_file_args = {}

        for attr in dir(args):
            # Ignore non-argument attributes.
            if not attr.startswith('_'):
                self._config_file_args[attr] = getattr(args, attr)
        self._config.update(self._config_file_args)

    def set(self, name, value):
        self._config[name] = value

    def __getattr__(self, attr):
        # We use getattr because I perfer using attributes rather than strings
        # for getting items out of a large config. It leads to fewer bugs imo.
        if attr in dir(super(_Config, self)):
            return getattr(super(_Config, self), attr)
        else:
            if self._cli_args == self._unconfigured:
                # Since parse_args is cached, we don't need to cache it's call here.
                self._parse_commandline_args()
            elif self._config_file_args == self._unconfigured:
                self._parse_config_file()
            if attr in self._config:
                return self._config[attr]
            else:
                print(self._config)
                raise AttributeError('Could not find %s config value' % attr)

config = _Config()
constants = config.constants
constants.supported_isas = ['ARM', 'SPARC', 'X86', 'ALPHA', 'RISCV']


class Argument(object):
    '''
    Class represents a cli argument/flag for a argparse parser.

    :var name: The long name of this object that will be stored in the arg
    output by the final parser.
    '''
    def __init__(self, *flags, **kwargs):
        self.flags = flags
        self.kwargs = kwargs

        if len(flags) == 0:
            raise ValueError("Need at least one argument.")
        elif 'dest' in kwargs:
            self.name = kwargs['dest']
        elif len(flags) > 1 or flags[0].startswith('-'):
            for flag in flags:
                if not flag.startswith('-'):
                    raise ValueError("invalid option string %s: must start"
                    "with a character '-'" % flag)

                if flag.startswith('--'):
                    if not hasattr(self, 'name'):
                        self.name = flag.lstrip('-')

        if not hasattr(self, 'name'):
            self.name = flags[0].lstrip('-')
        self.name = self.name.replace('-', '_')

    def add_to(self, parser):
        parser.add_argument(*self.flags, **self.kwargs)
    def copy(self):
        return copy.deepcopy(self)

class _StickyInt:
    '''
    A class that is used to cheat the verbosity count incrementer by
    pretending to be an int. This likely has very limited utility outside of
    this use case.
    '''
    def __init__(self, val=0):
        self.val = val
        self.type = int
    def __add__(self, other):
        self.val += other
        return self

# A list of common arguments/flags used across cli parsers.
common_args = [
    Argument(
        'directory',
        help='Directory to start searching for tests in'),
    Argument(
        '--fail-fast',
        action='store_true',
        help='Stop running on the first instance of failure'),
    Argument(
        '--tags',
        action='append',
        default=[],
        help=None),
    Argument(
        '--build-dir',
        action='store',
        default='build',
        help='Build directory for SCons'),
    Argument(
        '--base-dir',
        action='store',
        default=os.path.abspath(os.path.join(helper.absdirpath(__file__),
                                             os.pardir, os.pardir)),
        help='Directory to change to in order to exec scons.'),
    Argument(
        '-j', '--threads',
        action='store',
        default=1,
        help='Number of threads to run SCons with.'),
    Argument(
        '-v',
        action='count',
        dest='verbose',
        default=_StickyInt(),
        help='Increase verbosity'),
    Argument(
        '--config-path',
        action='store',
        default=os.getcwd(),
        help='Path to read a testing.ini config in'
    ),
    Argument(
        '--skip-build',
        action='store_true',
        default=False,
        help='Skip the building component of SCons targets.'
    ),
]
# NOTE: There is a limitation which arises due to this format. If you have
# multiple arguments with the same name only the final one in the list will be
# saved.
# e.g. if you have a -v argument which increments verbosity level and
# a separate --verbose flag which 'store's verbosity level. the final one in the
# list will be saved.
common_args = _util.AttrDict({arg.name:arg for arg in common_args})


class ArgParser(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, parser):
        # Copy public methods of the parser.
        for attr in dir(parser):
            if not attr.startswith('_'):
                setattr(self, attr, getattr(parser, attr))
        self.parser = parser
        self.add_argument = self.parser.add_argument

        # Argument will be added to all parsers and subparsers.
        common_args.verbose.add_to(parser)


class CommandParser(ArgParser):
    '''
    Main parser which parses command strings and uses those to direct to
    a subparser.
    '''
    def __init__(self):
        parser = argparse.ArgumentParser()
        super(CommandParser, self).__init__(parser)
        self.subparser = self.add_subparsers(dest='command')


class RunParser(ArgParser):
    '''
    Parser for the \'run\' command.
    '''
    def __init__(self, subparser):
        parser = subparser.add_parser(
            'run',
            help='''Run Tests.'''
        )

        super(RunParser, self).__init__(parser)

        common_args.skip_build.add_to(parser)
        common_args.directory.add_to(parser)
        common_args.build_dir.add_to(parser)
        common_args.base_dir.add_to(parser)
        common_args.fail_fast.add_to(parser)
        common_args.threads.add_to(parser)

        # Modify the help statement for the tags common_arg
        mytags = common_args.tags.copy()
        mytags.kwargs['help'] = ('Only run items marked with one of the given'
                                 ' tags.')
        mytags.add_to(parser)


class ListParser(ArgParser):
    '''
    Parser for the \'list\' command.
    '''
    def __init__(self, subparser):
        parser = subparser.add_parser(
            'list',
            help='''List and query test metadata.'''
        )

        super(ListParser, self).__init__(parser)
        common_args.directory.add_to(parser)
        mytags = common_args.tags.copy()
        mytags.kwargs['help'] = ('Only list items marked with one of the'
                                 ' given tags.')
        mytags.add_to(parser)


# Setup parser and subcommands
baseparser = CommandParser()
runparser = RunParser(baseparser.subparser)
listparser = ListParser(baseparser.subparser)
