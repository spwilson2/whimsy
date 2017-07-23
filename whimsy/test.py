import abc
from unittest import FunctionTestCase as _Ftc
from functools import partial

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


class TestCase(object):
    '''
    Test Base Class.

    All tests for must derive from this base class in order for them to be
    enumerated by the test system.
    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, fixtures=None):
        '''
        '''
        if isinstance(fixtures, list):
            fixtures = {fixture.name: fixture for fixture in fixtures}
        elif fixtures is None:
            fixtures = {}
        self.fixtures = fixtures

    @abc.abstractmethod
    def test(self, result, fixtures):
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

    def test(self, result, fixtures):
        self._test_function(result, fixtures)

    @property
    def name(self):
        return self._name

#TestFunction('')

def testfunction():
    '''Decorator used to mark a function as a test case.'''
    #TODO
    pass


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
