import abc
import copy
from unittest import FunctionTestCase as _Ftc
from functools import partial

from config import config
import helper
import fixture

def steal_unittest_assertions(module):
    '''
    Attach all the unittest.TestCase assertion helpers to the given modules
    namespace.
    '''
    # Since unittest assertion helpers all need an instance to work, we
    # need to do some partial application with a wrapper function.
    fake_testcase = _Ftc(None)
    for item in dir(_Ftc):
        if item.startswith('assert'):
            module[item] = partial(getattr(_Ftc, item), fake_testcase)

# Export the unittest assertion helpers from this module.
steal_unittest_assertions(globals())

class TestingException(Exception):
    '''Common ancestor for manual Testing Exceptions.'''
class TestFailException(TestingException):
    '''Signals that a test has failed.'''
class TestSkipException(TestingException):
    '''Signals that a test has been skipped.'''

def fail(message):
    '''Cause the current test to fail with the given message.'''
    raise TestFailException(message)

def skip(message):
    '''Cause the current test to skip with the given message.'''
    raise TestSkipException(message)


class TestCase(object):
    '''
    Test Base Class.

    All tests for must derive from this base class in order for them to be
    enumerated by the test system.
    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, tags=None, fixtures=None):
        '''
        All subclasses must call this __init__ method for them to be
        enumerated by the test loader.
        '''
        if fixtures is None:
            fixtures = {}
        elif not isinstance(fixtures, dict):
            fixtures = {fixture.name: fixture for fixture in fixtures}
        self.fixtures = fixtures
        if tags is None:
            tags = set()
        self.tags = set(tags)

    @abc.abstractmethod
    def test(self, fixtures):
        pass

    @abc.abstractproperty
    def name(self):
        pass

def gem5_test(test,
              tags=None,
              fixtures=None,
              valid_isas=None,
              valid_optimizations=('opt',),
              fixup_callback=None):
    '''
    Common test generator used to perform create tests for generic Gem5
    testing.

    :param test: Function to use for testing.

    :param tags: Iterable of tags which will be attached to all test cases
    generated.

    :param fixtures: In addtional to all requested fixtures, the gem5.opt
    binary will be provided.

    :param valid_isas: If arch is not set assumes that the test will be
    available for all ISAs. (And will create individual tests for
    each ISA.)

    :param valid_optimizations: If optimizations is not set assumes that the
    test only works for 'gem5.opt' targets.

    :param config: Config file to use for Gem5.
    :param config_args: List of arguments to pass to the config file.
    :param gem5_args: List of arguments to pass to gem5.

    :param fixup_callback: A final callback to make before creating each
    instance of a testfunction. The callback is handed the kwargs as well as
    the isa and optimization level which will be handed to instantiate
    a TestFunction. This allows you to modify the arguments before they are
    passed. (One such use case is to create additional fixtures based on isa.)
    The callback should look like:
    .. :code-block: python
        def callback(kwargs : dict, isa : str, optimization : str) -> None:
            pass

    '''

    if valid_isas is None:
        valid_isas = config.constants.supported_isas

    fixtures = [] if fixtures is None else fixtures

    # TODO: assert that the valid_optimizations are all valid

    for opt in valid_optimizations:
        for isa in valid_isas:
            # Create the gem5 target for the specific architecture and
            # optimization level.
            fixtures = copy.copy(fixtures)
            fixtures.append(fixture.Gem5Fixture(isa, opt))
            if fixup_callback is not None:
                fixup_callback(kwargs, isa, opt)
            TestFunction(test, fixtures=fixtures)

def Gem5ProgramTest(name, program, config):
    '''
    Runs the given program using the given config and passes if no exception
    was thrown.

    Note this is not an actual testcase, it generates a test function which
    can be used by gem5_test.

    :param name: Name of the test.
    :param config: The config to give gem5.
    :param program: The executable to run using the config.
    '''

class TestFunction(TestCase):
    '''
    Class which wraps functions to use as a test case.
    '''
    def __init__(self, test, name=None, *args, **kwargs):
        super(TestFunction, self).__init__(*args, **kwargs)
        self._test_function = test
        if name is None:
            name = test.__name__
        self._name = name

    def test(self, fixtures):
        self._test_function(fixtures)

    @property
    def name(self):
        return self._name

def testfunction(function=None, name=None, tag=None, tags=None, fixtures=None):
    # If tag was given, then the test will be marked with that single tag.
    # elif tags was given, then the test will be marked with all those tags.
    if tag is not None:
        tags = set((tag,))
    elif tags is not None:
        tags = set(tags)

    def testfunctiondecorator(function):
        '''Decorator used to mark a function as a test case.'''
        TestFunction(function, name=name, tags=tags, fixtures=fixtures)
        return function
    if function is not None:
        return testfunctiondecorator(function)
    else:
        return testfunctiondecorator

def tag():
    '''Decorator to add a tag to a test case.'''
    pass


if __name__ == '__main__':
    print('Self-test')
    print('Test that we can create a dereived tests from TestCase.')
    class NewBase(TestCase):
        def test(self, fixtures):
            pass

    print('Test that a test must have the test method defined.')
    try:
        class NewBase(TestCase):
            pass
    except:
        pass
    else:
        assert False, 'Did not raise an exception for an undefined test method.'
