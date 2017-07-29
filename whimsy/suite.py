import os

import _util
if __debug__:
    import test

class TestSuite(object):
    '''An object containing a collection of tests.'''
    def __init__(self, name, testcases=tuple(), tags=None, fixtures=None):
        '''
        :param testcases: An iterable of TestCase or TestSuite objects.
        :param name: Name of the TestSuite

        :param failfast: If True indicates the first test to fail in the test
        suite will cause the execution of the test suite to halt.
        '''
        self.testcases = []
        self.testcases.extend(testcases)

        self._name = name

        if fixtures is None:
            fixtures = {}
        elif not isinstance(fixtures, dict):
            fixtures = {fixture.name: fixture for fixture in fixtures}
        self.fixtures = fixtures

        if tags is None:
            tags = set()
        self.tags = set(tags)

        self._path = os.getcwd()

    @property
    def name(self):
        return self._name
    @property
    def path(self):
        return self._path
    @property
    def uid(self):
        return _util.uid(self)

    def __iter__(self):
        return iter(self.testcases)
    def __len__(self):
        return len(self.testcases)
    def append(self, item):
        self.testcases.append(item)
    def extend(self, items):
        self.testcases.extend(items)


class SuiteCollection(list):
    '''
    Container class for test suites which provides some utility functions and
    metadata.
    '''
    def __init__(self, suites=tuple()):
        super(SuiteCollection, self).__init__(suites)

    def iter_fixtures(self):
        '''
        Return an iterable of all fixtures of all suites' testcases in this
        collection.

        NOTE: May return duplicates if fixtures are duplicated across test
        cases.
        '''
        for suite in self:
            for testcase in suite:
                for fixture in testcase.fixtures.values():
                    yield fixture

if __name__ == '__main__':
    TestSuite('')
    SuiteCollection()
