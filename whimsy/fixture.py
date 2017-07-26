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
import os

from config import config
import helper
import logger
import tempfile

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

class TempdirFixture(Fixture):
    default_name = 'tempdir'
    def __init__(self, name=None, **kwargs):
        name = self.default_name if name is None else name
        super(TempdirFixture, self).__init__(name, **kwargs)
        self.path = None

    def setup(self):
        self.path = tempfile.mkdtemp()


class SConsFixture(Fixture):
    '''
    Fixture will wait until all SCons targets are collected and tests are
    about to be ran, then will invocate a single instance of SCons for all
    targets.

    :param directory: The directory which scons will -C (cd) into before
    executing. If None is provided, will choose the config base_dir.
    '''
    def __init__(self, name='SCons Fixture', directory=None, *args, **kwargs):
        super(SConsFixture, self).__init__(name, *args, lazy_init=True)
        self.directory = config.base_dir if directory is None else directory
        self.targets = []

    @helper.cacheresult
    def setup(self):
        super(SConsFixture, self).setup()
        targets = set(self.required_by)
        command = ['scons', '-C', self.directory, '-j', str(config.threads)]
        command.extend([target.target for target in targets])
        logger.log.debug('Executing command: %s' % command)
        helper.log_call(command)

    def teardown(self):
        pass

# The singleton scons fixture we'll use for all targets.
scons = SConsFixture(lazy_init=False)

class SConsTarget(Fixture):
    def __init__(self, target, build_dir=None, invocation=scons, *args, **kwargs):
        '''
        Represents a target to be built by an 'invocation' of scons.

        :param target: The target known to scons.

        :param build_dir: The 'build' directory path which will be prepended
        to the target name.

        :param invocation: Represents an invocation of scons which we will
        automatically attach this target to. If None provided, uses the main
        'scons' invocation.
        '''

        if build_dir is None:
            build_dir = config.build_dir \
                    if hasattr(config, str(config.build_dir)) \
                    else os.path.abspath(os.path.join(config.basedir,
                                                      os.pardir, 'build'))

        self.target = os.path.join(build_dir, target)
        super(SConsTarget, self).__init__(self.target, *args, **kwargs)

        # Add our self to the required targets of the SConsFixture
        self.require(invocation)
        self.invocation = invocation

    def setup(self):
        super(SConsTarget, self).setup()
        self.invocation.setup()
        return self

class Gem5Fixture(SConsTarget):
    def __init__(self, isa, optimization):
        target = helper.joinpath(isa.upper(), 'gem5.%s' % optimization)
        super(Gem5Fixture, self).__init__(target)
        self.name = 'gem5'
        self.path = self.target
        self.isa = isa
        self.optimization = optimization

    def setup(self):
        if config.skip_build:
            logger.log.debug('Skipping build of %s' % self.target)
        else:
            super(Gem5Fixture, self).setup()
