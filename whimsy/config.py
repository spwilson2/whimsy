import abc
import argparse
import copy
import os
from pickle import HIGHEST_PROTOCOL as highest_pickle_protocol

from helper import cacheresult, absdirpath
from _util import AttrDict

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
    _defaults = AttrDict()
    __shared_dict = {}
    constants = AttrDict()

    def __init__(self):
        self.__dict__ = self.__shared_dict

    @cacheresult
    def _parse_config_file(self):
        # TODO: Add support for config files.
        self._config_file_args = None

    @cacheresult
    def _parse_commandline_args(self):
        args = baseparser.parse_args()
        # Finish up our verbose args incrementing hack.
        args.verbose = args.verbose.val
        self._config_file_args = {}
        self._cli_args = {}

        for attr in dir(args):
            # Ignore non-argument attributes.
            if not attr.startswith('_'):
                self._config_file_args[attr] = getattr(args, attr)
        self._config.update(self._config_file_args)

        self._defaults.build_dir = os.path.join(self.base_dir, 'build')

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
            elif hasattr(self._defaults, attr):
                return getattr(self._defaults, attr)
            else:
                raise AttributeError('Could not find %s config value' % attr)


config = _Config()
# Defaults are provided by the config if the attribute is not found in the
# config or commandline. For instance, if we are using the list command
# fixtures might not be able to count on the build_dir being provided since we
# aren't going to build anything.
_defaults = config._defaults
constants = config.constants
_defaults.base_dir = os.path.abspath(os.path.join(absdirpath(__file__),
                                                  os.pardir,
                                                  os.pardir))
_defaults.result_path = os.path.join(os.getcwd(), '.testing-results')
_defaults.list_only_failed = False


constants.system_out_name = 'system-out'
constants.system_err_name = 'system-err'
constants.x86_tag = 'X86'
constants.sparc_tag = 'SPARC'
constants.alpha_tag = 'ALPHA'
constants.riscv_tag = 'RISCV'
constants.arm_tag = 'ARM'
constants.supported_isas = [
    constants.x86_tag,
    constants.sparc_tag,
    constants.alpha_tag,
    constants.riscv_tag,
    constants.arm_tag
]

constants.tempdir_fixture_name = 'tempdir'
constants.gem5_simulation_stderr = 'simerr'
constants.gem5_simulation_stdout = 'simout'
constants.gem5_simulation_stats = 'stats.txt'
constants.gem5_simulation_config_ini = 'config.ini'
constants.gem5_simulation_config_json = 'config.json'
constants.gem5_returncode_fixture_name = 'gem5-returncode'
constants.gem5_binary_fixture_name = 'gem5'
constants.pickle_protocol = highest_pickle_protocol

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
        '--uid',
        action='store',
        default=None,
        help='UID of a specific test item to run.'),
    Argument(
        '--build-dir',
        action='store',
        default=None,
        # We need to manually set this default to config's
        # --base-dir/build
        help='Build directory for SCons'),
    Argument(
        '--base-dir',
        action='store',
        default=_defaults.base_dir,
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
    Argument(
        '--result-path',
        action='store',
        default=_defaults.result_path,
        help='The path to store results in.'
    ),
    Argument(
        '--list-only-failed',
        action='store_true',
        default=False,
        help='Only list tests that failed.'
    )
]

# NOTE: There is a limitation which arises due to this format. If you have
# multiple arguments with the same name only the final one in the list will be
# saved.
#
# e.g. if you have a -v argument which increments verbosity level and
# a separate --verbose flag which 'store's verbosity level. the final one in the
# list will be saved.
common_args = AttrDict({arg.name:arg for arg in common_args})


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

        common_args.uid.add_to(parser)
        common_args.skip_build.add_to(parser)
        common_args.directory.add_to(parser)
        common_args.build_dir.add_to(parser)
        common_args.base_dir.add_to(parser)
        common_args.fail_fast.add_to(parser)
        common_args.threads.add_to(parser)
        common_args.list_only_failed.add_to(parser)

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

        Argument(
            '--suites',
            action='store_true',
            default=False,
            help='List all test suites.'
        ).add_to(parser)
        Argument(
            '--tests',
            action='store_true',
            default=False,
            help='List all test cases.'
        ).add_to(parser)
        Argument(
            '--fixtures',
            action='store_true',
            default=False,
            help='List all fixtures.'
        ).add_to(parser)

        common_args.directory.add_to(parser)
        mytags = common_args.tags.copy()
        mytags.kwargs['help'] = ('Only list items marked with one of the'
                                 ' given tags.')
        mytags.add_to(parser)


class RerunParser(ArgParser):
    def __init__(self, subparser):
        parser = subparser.add_parser(
            'rerun',
            help='''Rerun failed tests.'''
        )
        super(RerunParser, self).__init__(parser)

        common_args.skip_build.add_to(parser)
        common_args.directory.add_to(parser)
        common_args.build_dir.add_to(parser)
        common_args.base_dir.add_to(parser)
        common_args.fail_fast.add_to(parser)
        common_args.threads.add_to(parser)
        common_args.list_only_failed.add_to(parser)


# Setup parser and subcommands
baseparser = CommandParser()
runparser = RunParser(baseparser.subparser)
listparser = ListParser(baseparser.subparser)
rerunparser = RerunParser(baseparser.subparser)
