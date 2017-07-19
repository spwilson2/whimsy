# Suites should have ability to be parallelized...
# Suites should provide fixtures for their contained test cases..
# How?

class TestSuite(object):
    '''An object containing a collection of tests or other test suites.'''
    top_level = None
    __instances = []

    def __init__(self, name, *items):
        '''
        All test suites are implicitly added into the top_level TestSuite.
        This forms a DAG so test runners can traverse this running test suite
        collections.

        :param items: A list of TestCase classes or TestSuite objects.

        :param name:
        '''
        self.items = list()
        self.add_items(*items)
        self.name = name
        TestSuite.__instances.append(self)

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

TestSuite.top_level = TestSuite('Whimsy Test Suite')
