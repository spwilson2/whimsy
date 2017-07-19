import abc
import inspect

VALID_TEST_FUNCTION_SIGNATURES = []
class _ValidTestSignatures(object):
    def test(self, fixtures):
        pass
    VALID_TEST_FUNCTION_SIGNATURES.append(inspect.getargspec(test))

def _check_test_signature(metaclass, clsname, bases, dct):
    if metaclass.__original_base__ is not None:
        if not 'test' in dct:
            assert(False)
        if inspect.getargspec(dct['test']) not in VALID_TEST_FUNCTION_SIGNATURES:
            assert(False)

    return metaclass, clsname, bases, dct

class TestBase(object):
    '''
    Test Base Class.

    All tests for must derive from this base class in order for them to be
    enumerated by the test system.
    '''

    # Use a metaclass to keep track of all derived tests and assert that test
    # classes have the correct signature.
    instances = []

    def __init__(self, fixtures=[]):
        '''
        '''
        self.fixtures = fixtures
        TestBase.instances.append(self)

    @staticmethod
    def list_all():
        return TestBase.instances


class TestFunction(TestBase):
    '''
    Class which wraps functions to use as a test case.
    '''
    def __init__(self, test, fixtures=[]):
        super(TestFunction, self).__init__(fixtures=fixtures)
        self._test_function = test

    def test(self, fixtures):
        self._test_function(self, fixtures)

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
    print('Test that we can create a dereived tests from TestBase.')
    class NewBase(TestBase):
        def test(self, fixtures):
            pass

    print('Test that a test must have the test method defined.')
    try:
        class NewBase(TestBase):
            pass
    except:
        pass
    else:
        assert False, 'Did not raise an exception for an undefined test method.'
