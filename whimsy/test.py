from abc import ABCMeta, abstractmethod
from os import getcwd

from suite import TestList
from unittest import FunctionTestCase as _Ftc
from functools import partial

from _util import uid

def _as_kwargs(**kwargs):
    return kwargs

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
    For example: in a test were we run gem5 and verify output. The combination
    of running gem5 and verifying output forms a TestCase. Whereas it would be
    imposible to run verify output if gem5 was not run first. In this example
    both gem5 and verify output would be subtests of a single TestCase.
    '''
    __metaclass__ = ABCMeta
    def __init__(self, name, tags=None, fixtures=None):
        '''
        __init__ must be called in subclasses for self contained tests to be
        recognized by the test loader.
        '''
        if fixtures is None:
            fixtures = {}
        elif not isinstance(fixtures, dict):
            fixtures = {fixture.name: fixture for fixture in fixtures}
        self.fixtures = fixtures

        if tags is None:
            tags = set()
        self.tags = set(tags)

        self._name = name
        self._path = getcwd()

    @property
    def uid(self):
        return uid(self)
    @property
    def path(self):
        return self._path
    @property
    def name(self):
        return self._name
    @abstractmethod
    def __call__(self, fixtures):
        pass
    # This is a method that will be created by the test loader in order to
    # manually remove a test.
    unregister = NotImplemented

class TestFunction(TestCase):
    __metaclass__ = ABCMeta
    def __init__(self, test, name=None, *args, **kwargs):
        if name is None:
            # If not given a name, take the name of the function.
            name = test.__name__
        super(TestFunction, self).__init__(name, *args, **kwargs)
        self._test_function = test

    def __call__(self, fixtures):
        '''
        Override TestCase definition of __call__
        '''
        self._test_function(fixtures)


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
        assert False, ('Did not raise an exception'
                       ' for an undefined test method.')
