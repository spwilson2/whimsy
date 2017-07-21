import abc
import argparse
import numbers

class ArgParser(object):
    __metaclass__ = abc.ABCMeta
    def __init__(self, parser):
        self.parser = parser
        self.add_argument = self.parser.add_argument

    @abc.abstractmethod
    def setup(self):
        pass
    @abc.abstractmethod
    def parse(self):
        pass

class RunParser(ArgParser):
    def __init__(self, subparser):
        parser = subparser.add_parser(
            'run',
            help=''''''
        )
        super(RunParser, self).__init__(parser)

    def setup(self):
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

    def setup(self):
        pass

    def parse(self):
        pass

class Argument:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    def add_to_parser(self, parser):
        parser.add_argument(*self.args, **self.kwargs)

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

def parse_args():
    # Setup parser and subcommands
    baseparser = argparse.ArgumentParser()
    subparser = baseparser.add_subparsers()
    parsers = [RunParser(subparser), ListParser(subparser)]

    verbosity = 0
    verbose_arg = Argument('--verbose', '-v',
                           action='count',
                           default=_SickyInt(),
                           help='Increase verbosity')

    for parser in parsers:
        parser.setup()
        verbose_arg.add_to_parser(parser)
    verbose_arg.add_to_parser(baseparser)

    args = baseparser.parse_args()
    args.verbose = args.verbose.val
    return args
