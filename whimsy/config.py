'''
Note: This module is atypical. It replaces its own namespace with
a ConfigModule object in order to export the config in a user friendly way (as
a property).
'''

import abc
import argparse
import numbers
import sys
import types

import helper
import _util

class Flag(_util.Enum):
    def __init__(self, option):
        self.flag = flag
    def asflag(self):
        return '--' + str(self)
    def __str__(self):
        return self.flag
    def __get__(self, instance, _):
        return instance.flag

flags = [
        'directory',
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

        super(RunParser, self).__init__(parser)

        self.add_argument('directory',
                          help='Directory to start'
                          ' searching for tests in')

class ListParser(ArgParser):
    def __init__(self, subparser):
        parser = subparser.add_parser(
            'list',
            help=''''''
        )
        super(ListParser, self).__init__(parser)

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

parsers = [RunParser(subparser), ListParser(subparser), baseparser]

@helper.cacheresult
def parse_args():
    for parser in parsers:
        verbose_arg.add_to_parser(parser)

    args = baseparser.parse_args()
    args.verbose = args.verbose.val
    return args

class _Config(object):
    '''
    Config object that automatically parses args when one attempts to get
    a config attr.
    '''
    def __getattr__(self, attr):
        # Since parse_args is cached, we don't need to cache it's call here.
        return getattr(parse_args(), attr)

config = _Config()
