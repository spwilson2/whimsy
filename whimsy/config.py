# TODO: Add support for using some kind of config file for testing.

# TODO: Refactor this module.
# Config should *probably* be separate from just arguments incase we add
# support for using files to configure testing.
import abc
import argparse
import numbers
import sys
import types

import helper
import _util

class _Config(object):
    '''
    Config object that automatically parses args when one attempts to get
    a config attr.
    '''
    _config = None
    def __getattr__(self, attr):
        if attr == '_config':
            return _Config._config
        else:
            if _Config._config is None:
                # Since parse_args is cached, we don't need to cache it's call here.
                _Config._config = parse_args()
            return getattr(_Config._config, attr)

config = _Config()

class Flag(_util.Enum):
    def __init__(self, flag):
        self.flag = flag
    def asflag(self):
        return '--' + str(self)
    def asarg(self):
        return str(self)
    def __str__(self):
        return self.flag
    @property
    def set(self):
        '''Checks if the given flag was set in the config.'''
        return getattr(config, str(self))

flags = [
        'directory',
        'failfast',
        'tags'
        ]

for flag in flags:
    setattr(Flag, flag, Flag(flag))

class ArgParser(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, parser):
        self.parser = parser
        self.add_argument = self.parser.add_argument

    def parse(self):
        '''
        Function called once the top level parse has been called. We can now
        check our own args.
        '''
        return self.parser.parse_args()

class RunParser(ArgParser):
    def __init__(self, subparser):
        parser = subparser.add_parser(
            'run',
            help=''''''
        )
        parser.set_defaults(run=True)

        super(RunParser, self).__init__(parser)

        self.add_argument(
                Flag.directory.asarg(),
                help='Directory to start searching for tests in')
        self.add_argument(
                Flag.failfast.asflag(),
                action='store_true',
                help='Stop running on the first instance of failure')
        self.add_argument(
                Flag.tags.asflag(),
                action='append',
                default=[],
                help='Only run items marked with one of the given tags.')

class ListParser(ArgParser):
    def __init__(self, subparser):
        parser = subparser.add_parser(
            'list',
            help=''''''
        )
        parser.set_defaults(list=True)

        super(ListParser, self).__init__(parser)

        self.add_argument(
                Flag.tags.asflag(),
                action='append',
                help='Only list items marked with one of the given tags.')
        self.add_argument(
                Flag.directory.asarg(),
                help='Directory to start searching for tests in')

class Argument:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    def add_to_parser(self, parser):
        parser.add_argument(*self.args, **self.kwargs)


# Setup parser and subcommands
baseparser = argparse.ArgumentParser()
subparser = baseparser.add_subparsers()

class _SickyInt:
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
verbose_arg = Argument('--verbose', '-v',
                       action='count',
                       default=_SickyInt(),
                       help='Increase verbosity')

baseparser.set_defaults(run=False, list=False)
parsers = [RunParser(subparser), ListParser(subparser), baseparser]

@helper.cacheresult
def parse_args():
    for parser in parsers:
        verbose_arg.add_to_parser(parser)

    args = baseparser.parse_args()
    args.verbose = args.verbose.val
    return args
