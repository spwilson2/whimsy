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
        super(MakeFixture, self).__init__(cached=True, lazy_init=False,
                                          *args, **kwargs)
        self.targets = []

    def setup(self):
        super(MakeFixture, self).setup()
        targets = set(self.required_by)
        command = ['make']
        command.extend([target.target for target in targets])
        logger.log.debug('Executing command: %s' % command)
        helper.log_call(command)


class MakeTarget(fixture.Fixture):
    # The singleton make fixture we'll use for all targets.
    make_fixture = MakeFixture('Global Make Fixture')

    def __init__(self, target, *args, **kwargs):
        super(MakeTarget, self).__init__(name=target, *args, **kwargs)
        self.target = self.name

        # Add our self to the required targets of the main MakeFixture
        #make_fixture.add_target(self)
        self.require(self.make_fixture)

    def setup(self):
        fixture.Fixture.setup(self)
        self.make_fixture.setup()
        return self


first_fixture = [
    MakeTarget('first-target'),
]

second_fixture = [
    MakeTarget('second-target'),
]


def simple_test(result, fixtures):
    print 'Simple Test!!'

def simple_fail_test(result, fixtures):
    test.assertTrue(False)

print('running code in simple2-test.py')
TESTS = [
    test.TestFunction(simple_test, fixtures=second_fixture),
    test.TestFunction(simple_test, fixtures=first_fixture),
    test.TestFunction(simple_fail_test),
]
