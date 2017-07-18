import abc
import inspect
import _util

VALID_TEST_FUNCTION_SIGNATURES = []
class _ValidSignatureExamples(object):
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

_TestBaseMetaclass = _util.create_collector_metaclass(
        '_TestBaseMetaclass',
        callback=_check_test_signature)

class TestBase(object):
    '''
    Test Base Class.

    All tests for must derive from this base class in order for them to be
    enumerated by the test system.
    '''

    # Use a metaclass to keep track of all derived tests
    __metaclass__ = _TestBaseMetaclass

    def __init__(self, setup=None, teardown=None):
        '''
        :param setup: Function to be performed before the test case.
        The test case will recieve the setup return value as an argument.

        :param teardown: Function to be performed after the test case.
        Teardown recieves the result of the test case as an argument.
        '''
        pass

    def require_fixture(self):
        '''
        Add a given fixture to the list of required fixtures for this
        test.
        '''


class TestFunction(TestBase):
    '''
    Class which wraps functions to use as a test case.
    '''
    #TODO
    def test(self, fixtures):
        pass


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
