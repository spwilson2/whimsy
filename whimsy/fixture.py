# Requirements for Fixtures:
#
# - Should be able to specify level of caching (Global, Test Suite, or Test
# Case, None [Equivalent to Test Case])
#   - Should be able to attach fixtures to test cases, suites or make globally
#   available.
# - Optional (default) lazy_creation for delayed initialization - no reason to
# make 40 temp dirs at the startup.
# - Fixtures should be able to rely on other fixtures - all gem5 targets should
# rely on scons, and scons can then be ran just before the initial test.
#
# Examples of Fixtures:
# - Gem5 (built, then cached)
# - Linux Images (downloaded, then cached)
# - Test Programs (built, then cached)
# - Gold Standard Files (possibly downloaded or in directory, cached)
# - Temporary Directory
#
# Questions:
# How to specify test requires fixture?
# - TestCase have list of required fixtures
# - Decorator for class with the required fixture?
#
# How do we access the fixtures from test cases which require them?
# - Import them into the test class.
#
class CacheLevel:
    # Should this just be moved into implicitly how fixtures are used? I.e.
    # attached to either suites or standalone?
    _inc = iter(int, 1)
    Global = _inc.next()
    Suite = _inc.next()
    Case = _inc.next()


class Fixture(object):
    '''Base Class for a test Fixture'''
    def __init__(self, cached=None, lazy_init=True):
        '''
        :param lazy_init: If True, wait until test cases that use this fixture
        are ran to setup this fixture. Otherwise init the fixture before the
        first test case is ran.

        :var requires: List of fixtures which require this Fixture.
        :var required_by: List of fixtures this Fixture requires.
        '''
        self._requires = []
        self._required_by = []
        pass

    def import(self):
        '''Import the given fixture for use.'''
        pass

    def require(self, other_fixture):
        self._required_by
