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
import helper

class Fixture(object):
    '''Base Class for a test Fixture'''
    def __init__(self, name, cached=False, lazy_init=True):
        '''
        :param lazy_init: If True, wait until test cases that use this fixture
        are ran to setup this fixture. Otherwise init the fixture before the
        first test case is ran.

        :param cached: Cached means that the setup for this fixture will be
        cached. That is, multiple calls to setup will return a cachedresult.

        :var requires: List of fixtures which require this Fixture.
        :var required_by: List of fixtures this Fixture requires.
        '''
        self.requires = []
        self.required_by = []
        self.name = name
        self.built = False
        self.lazy_init = lazy_init

        if cached:
            self.setup = helper.cacheresult(self.setup)

    def require(self, other_fixture):
        self.requires.append(other_fixture)
        other_fixture.required_by.append(self)

    def setup(self):
        '''Call setup of fixtures we require.'''
        self.built = True
        for fixture in self.requires:
            fixture.setup()

    def teardown(self):
        '''Empty method, meant to be overriden if fixture requires teardown.'''
