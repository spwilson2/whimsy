import os
import subprocess

import whimsy.test as test
import whimsy.fixture as fixture
import whimsy.runner as runner
import whimsy.loader as loader

#class MakeFixture(fixture.Fixture):
#    '''
#    Fixture should wait until all make targets are collected and tests are
#    about to be ran, then should invocate a single instance of make for all
#    targets.
#    '''
#    def __init__(self, *args, **kwargs):
#        super(MakeFixture, self).__init__(*args, **kwargs)
#        self.targets = []
#
#    def add_target(self, target):
#        self.targets.append(target)
#
#    def setup(self):
#        targets = set(self.targets)
#        command = ['make']
#        command.extend(targets)
#        subprocess.check_call(command)
#
#    def teardown(self):
#        pass
#
## The singleton make fixture we'll use for all targets.
#make_fixture = MakeFixture(lazy_init=False)
#
#class MakeTarget(fixture.Fixture):
#
#    def __init__(self, target, *args, **kwargs):
#        super(MakeTarget, self).__init__(*args, **kwargs)
#        self.target = target
#
#        # Add our self to the required targets of the main MakeFixture
#        make_fixture.add_target(self)
#
#
#fixtures = [
#    MakeTarget('first-target'),
#    MakeTarget('second-target'),
#]


def simple_test(test, fixtures):
    # TODO: Check that our fixtures were created.
    print 'Simple Test!!'
    assert True

testloader = loader.TestLoader()
files = testloader.discover_files(os.path.dirname(os.path.abspath(__name__)))
for f in files:
    testloader.load_file(f)

testrunner = runner.Runner()
testrunner.run_all()
