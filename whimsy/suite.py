# Suites should have ability to be parallelized...
# Suites should provide fixtures for their contained test cases..
# How?

import _util
import os

if __debug__:
    import test

class TestSuite(object):
    clsname = 'Testsuite'

    '''An object containing a collection of tests or other test suites.'''
    def __init__(self, name, items=None, tags=None, fixtures=None,
                 failfast=True, self_contained=None):
        '''
        This forms a DAG so test runners can traverse this running test suite
        collections.

        :param items: An iterable of TestCase or TestSuite objects.
        :param name: Name of the TestSuite

        :param failfast: If True indicates the first test to fail in the test
        suite will cause the execution of the test suite to halt.

        :param self_contained: Indicates that this entire TestSuite does not
        rely on any parent suites to be reran. Defaults to failfast value if
        None given.

        :ivar self_contained: Means that when tests are reran to update FAIL
        outcome, this suite and all of its children form an top level entity
        that will be ran.
        '''

        self.name = name
        self.items = []
        self.failfast = failfast
        self.path = os.getcwd()

        if fixtures is None:
            fixtures = {}
        elif not isinstance(fixtures, dict):
            fixtures = {fixture.name: fixture for fixture in fixtures}
        self.fixtures = fixtures

        if tags is None:
            tags = set()
        self.tags = set(tags)

        if items is not None:
            self.add_items(*items)

        # TODO: Either update description or think of way to assert that we
        # don't rely on parent fixtures.
        if self_contained is None:
            self_contained = failfast
        self.self_contained = self_contained

    @property
    def uid(self):
        return _util.uid(self)

    def add_items(self, *items):
        '''Add the given items (TestCases or TestSuites) to this collection'''

        if __debug__:
            for item in items:
                if not (isinstance(item, TestSuite) or
                        isinstance(item, test.TestCase)):
                    raise AssertionError('Test Suite can only contain'
                                         ' TestSuite or TestCase.')

            # Check that we have not accidentally created a cycle of
            # testsuites. They should form a DAG in order for deepcopy and
            # other program logic to work.
            self._detect_cycle()
        self.items.extend(items)

    if __debug__:
        def _detect_cycle(self):
            '''
            Traverse the DAG looking for cycles.

            Note: Since we don\'t currently allow duplicates in test suites, this
            logic is simple and we can just check that there are no duplicates as
            we recurse down the tree.
            '''
            collected_set = set()
            def recursive_check(test_suite):
                if type(test_suite) == TestSuite:
                    for item in test_suite:
                        if item in collected_set:
                            return True
                        collected_set.add(item)
                        recursive_check(item)
                return False
            return recursive_check(self)

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def iter_inorder(self):
        '''
        Iterate over all the testsuites and testcases contained in this
        testsuite. Traverses the tree in in-order fashion.
        '''
        return _util.iter_recursively(self, inorder=True)

    def iter_leaves(self):
        '''
        Recursively iterate over all the testcases contained in this
        testsuite and testsuites we contain.
        '''
        return _util.iter_recursively(self, inorder=False)

    def enumerate_fixtures(self):
        '''
        Traverse all our subsuites and testcases and return a list of all
        their fixtures.
        '''
        fixtures = []
        for item in self.items:
            if isinstance(item, TestSuite):
                fixtures.extend(item.enumerate_fixtures())
            else:
                fixtures.extend(item.fixtures.values())
        return fixtures
