from helper import cacheresult

class Fixture(object):
    '''Base Class for a test Fixture'''
    def __init__(self, name, cached=False, lazy_init=True):
        # TODO: Should probably rename cached to buildonce or something as
        # such.
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
            self.setup = cacheresult(self.setup)

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

    # This is a method that will be created by the test loader in order to
    # manually remove a fixture.
    deregister = NotImplemented
