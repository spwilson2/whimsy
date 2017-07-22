import os
import subprocess
#import sys

import whimsy.test as test
import whimsy.fixture as fixture
import whimsy.runner as runner
import whimsy.loader as loader
import whimsy.logger as logger
import whimsy.helper as helper

class MakeFixture(fixture.Fixture):
    '''
    Fixture should wait until all make targets are collected and tests are
    about to be ran, then should invocate a single instance of make for all
    targets.
    '''
    def __init__(self, *args, **kwargs):
        super(MakeFixture, self).__init__(*args, **kwargs)
        self.targets = []

    @fixture.cacheresult
    def setup(self):
        super(MakeFixture, self).setup()
        targets = set(self.required_by)
        command = ['make']
        command.extend([target.target for target in targets])
        logger.log.debug('Executing command: %s' % command)
        helper.log_call(command)

    def teardown(self):
        pass


# The singleton make fixture we'll use for all targets.
make_fixture = MakeFixture(lazy_init=False)

class MakeTarget(fixture.Fixture):

    def __init__(self, target, *args, **kwargs):
        super(MakeTarget, self).__init__(*args, **kwargs)
        self.target = target

        # Add our self to the required targets of the main MakeFixture
        #make_fixture.add_target(self)
        self.require(make_fixture)

    def setup(self):
        fixture.Fixture.setup(self)
        make_fixture.setup()
        return self


first_fixture = {
    'first-target': MakeTarget('first-target'),
}

second_fixture = {
    'second-target': MakeTarget('second-target'),
}


def simple_test(result, fixtures):
    # TODO: Check that our fixtures were created.
    print 'Simple Test!!'
    assert True

def simple_fail_test(result, fixtures):
    assert False
    pass

print('running code in simple2-test.py')
TESTS = [
    test.TestFunction(simple_test, fixtures=second_fixture),
    test.TestFunction(simple_test, fixtures=first_fixture),
    test.TestFunction(simple_fail_test),
]
