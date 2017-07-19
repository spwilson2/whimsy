import abc

class TestCase(object):
    '''
    Test Base Class.

    All tests for must derive from this base class in order for them to be
    enumerated by the test system.
    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, fixtures={}):
        '''
        '''
        self.fixtures = fixtures

    @abc.abstractmethod
    def test(self, result, fixtures):
        pass

class TestFunction(TestCase):
    '''
    Class which wraps functions to use as a test case.
    '''
    def __init__(self, test, *args, **kwargs):
        super(TestFunction, self).__init__(*args, **kwargs)
        self._test_function = test

    def test(self, result, fixtures):
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
