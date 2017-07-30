from os import getcwd

from _util import uid

class TestSuite(object):
    '''An object containing a collection of tests.'''
    def __init__(self, name, tests=tuple(), tags=None, fixtures=None,
            fail_fast=True):
        '''
        :param testcases: An iterable of TestCase or TestSuite objects.
        :param name: Name of the TestSuite

        :param fail_fast: If True indicates the first test to fail in the test
        suite will cause the execution of the test suite to halt.
        '''
        self.testlist = TestList(tests)
        self.fail_fast = fail_fast

        self._name = name

        if fixtures is None:
            fixtures = {}
        elif not isinstance(fixtures, dict):
            fixtures = {fixture.name: fixture for fixture in fixtures}
        self.fixtures = fixtures

        if tags is None:
            tags = set()
        self.tags = set(tags)

        self._path = getcwd()

    @property
    def name(self):
        return self._name
    @property
    def path(self):
        return self._path
    @property
    def uid(self):
        return uid(self)

    @property
    def testcases(self):
        return tuple((testcase for testcase in self))
    def iter_testlists(self):
        return self.testlist.iter_keep_containers()
    def __iter__(self):
        return iter(self.testlist)
    def __len__(self):
        return len(self.testlist)
    def append(self, item):
        self.testlist.append(item)
    def extend(self, items):
        self.testlist.extend(items)


class SuiteList(object):
    '''
    Container class for test suites which provides some utility functions and
    metadata.
    '''
    def __init__(self, suites=[]):
        self.suites = []
        self.suites.extend(suites)

    def __iter__(self):
        return iter(self.suites)
    def __len__(self):
        return len(self.suites)
    def append(self, item):
        self.suites.append(item)
    def extend(self, items):
        self.suites.extend(items)

    def iter_fixtures(self):
        '''
        Return an iterable of all fixtures of all suites' testcases in this
        collection.

        NOTE: May return duplicates if fixtures are duplicated across test
        cases.
        '''
        for suite in self:
            for testcase in suite.testcases:
                for fixture in testcase.fixtures.values():
                    yield fixture

    def __add__(self, other):
        return SuiteList(super(list, self).__add__(self, other))

class TestList(object):
    '''
    Container class for `TestCase`s which provides some utility functions and
    metadata. `TestList`s can be heirarchical, in which case iteration returns
    just tests in in-order traversal.
    '''
    def __init__(self, items=[], fail_fast=False):
        self.fail_fast = fail_fast
        self.items = []
        if isinstance(items, TestList):
            self.append(items)
        else:
            self.extend(items)

    def _iter(self, keep_containers):

        # We can't use the _util iter_recursively function to do this since we
        # have defined a unusual __iter__
        for item in self.items:
            if isinstance(item, TestList):
                # Recurse into that list.
                for item_of_item in item._iter(keep_containers):
                    yield item_of_item
            else:
                if keep_containers:
                    yield (self, item)
                else:
                    yield item

    def iter_keep_containers(self):
        return self._iter(True)

    def iter_tests(self):
        return self._iter(False)

    def __iter__(self):
        return self.iter_tests()
    def __len__(self):
        return len(self.items)
    def append(self, item):
        self.items.append(item)
    def extend(self, items):
        self.items.extend(items)
