import abc
from unittest import FunctionTestCase as _Ftc
from functools import partial

import helper

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
