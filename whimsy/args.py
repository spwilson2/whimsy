import abc
import argparse
import numbers

class ArgParser(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, parser):
        self.parser = parser
        self.add_argument = self.parser.add_argument

    @abc.abstractmethod
    def parse(self):
        '''
        Function called once the top level parse has been called. We can now
        check our own args.
        '''
        pass

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

    def parse(self):
        pass

class ListParser(ArgParser):
    def __init__(self, subparser):
        parser = subparser.add_parser(
            'list',
            help=''''''
        )
        super(ListParser, self).__init__(parser)

    def parse(self):
        pass

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

for parser in parsers:
    verbose_arg.add_to_parser(parser)

args = baseparser.parse_args()
args.verbose = args.verbose.val
