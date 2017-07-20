# Suites should have ability to be parallelized...
# Suites should provide fixtures for their contained test cases..
# How?

import whimsy._util as util

class TestSuite(object):
    '''An object containing a collection of tests or other test suites.'''
    def __init__(self, name, items=None, failfast=True, parallelizable=False):
        '''
        All test suites are implicitly added into the top_level TestSuite.
        This forms a DAG so test runners can traverse this running test suite
        collections.

        :param items: A list of TestCase classes or TestSuite objects.

        :param name:

        :param failfast: If True indicates the first test to fail in the test
        suite will cause the execution of the test suite to halt.

        :param paralleizable: keyword only arg - indicates that tests and
        suites contained within are parallelizable with respect to eachother.
        '''

        self.name = name
        self.fixtures = {}
        self.items = []
        self.failfast = failfast
        self.parallelizable = parallelizable

        if items is not None:
            self.add_items(*items)

    def add_items(self, *items):
        '''Add the given items (TestCases or TestSuites) to this collection'''
        self.items.extend(items)

    def require_fixture():
        '''
        Require the given fixture to run this test suite and all its
        elements.
        '''
        pass

    @classmethod
    def list_all(cls):
        '''Return all instances of this class.'''
        return cls.__instances

    def _detect_cycle(self):
        '''
        Traverse the DAG looking for cycles.

        Note: Since we don\'t currently allow duplicates in test suites, this
        logic is simple and we can just check that there are no duplicates.
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

    def copy(self):
        '''
        We don't create deep copies of tests, we just create copies of the
        containers of references.
        '''
        newcopy = TestSuite(self.name,
                            self.items[:],
                            self.failfast,
                            self.parallelizable)
        newcopy.fixtures = self.fixtures.copy()
        return newcopy
