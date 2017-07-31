import os
import tempfile

from ..fixture import Fixture
from ..config import config
from ..helper import log_call, cacheresult, joinpath
from ..logger import log


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

    @cacheresult
    def setup(self):
        super(SConsFixture, self).setup()
        targets = set(self.required_by)
        command = ['scons', '-C', self.directory, '-j', str(config.threads)]
        command.extend([target.target for target in targets])
        log.debug('Executing command: %s' % command)
        log_call(command)

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
        target = joinpath(isa.upper(), 'gem5.%s' % optimization)
        super(Gem5Fixture, self).__init__(target)
        self.name = 'gem5'
        self.path = self.target
        self.isa = isa
        self.optimization = optimization

    def setup(self):
        if config.skip_build:
            log.debug('Skipping build of %s' % self.target)
        else:
            super(Gem5Fixture, self).setup()
