# Suites should have ability to be parallelized...
# Suites should provide fixtures for their contained test cases..
# How?
import _util

_TestSuiteMetaclass = _util.create_collector_metaclass('TestSuite',
                                                       save_inheritors=False,
                                                       save_instances=True)

class TestSuite(object):
    '''An object containing a collection of tests or other test suites.'''
    __metaclass__ = _TestSuiteMetaclass
    top_level = None

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

    def add_items(self, *items):
        '''Add the given items (TestCases or TestSuites) to this collection'''
        self.items.extend(items)

    def require_fixture():
        '''
        Require the given fixture to run this test suite and all its
        elements.
        '''
        pass

    @staticmethod
    def get_all():
        '''Return all instances of this class.'''
        return _TestSuiteMetaclass.__instances__

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
