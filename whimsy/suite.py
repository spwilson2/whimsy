import os

import _util
if __debug__:
    import test

class TestSuite(list):
    '''An object containing a collection of tests.'''
    clsname = 'Testsuite'

    def __init__(self, name, testcases=tuple(), tags=None, fixtures=None,
                 failfast=True):
        '''
        :param testcases: An iterable of TestCase or TestSuite objects.
        :param name: Name of the TestSuite

        :param failfast: If True indicates the first test to fail in the test
        suite will cause the execution of the test suite to halt.
        '''
        super(TestSuite, self).__init__(testcases)
        self.name = name
        self.failfast = failfast
        self.path = os.getcwd()
        self.testcases = self

        if fixtures is None:
            fixtures = {}
        elif not isinstance(fixtures, dict):
            fixtures = {fixture.name: fixture for fixture in fixtures}
        self.fixtures = fixtures

        if tags is None:
            tags = set()
        self.tags = set(tags)

    @property
    def uid(self):
        return _util.uid(self)

class SuiteCollection(list):
    '''
    Container class for test suites which provides some utility functions and
    metadata.
    '''
    def __init__(self, suites=tuple()):
        super(SuiteCollection, self).__init__(suites)

if __name__ == '__main__':
    TestSuite('')
    SuiteCollection()
