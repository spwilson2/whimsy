import os
import subprocess
#import sys

import testlib.test as test
import testlib.fixture as fixture
import testlib.runner as runner
import testlib.loader as loader
import testlib.logger as logger
import testlib.helper as helper
import testlib.suite as suite

class MakeFixture(fixture.Fixture):
    '''
    Fixture should wait until all make targets are collected and tests are
    about to be ran, then should invocate a single instance of make for all
    targets.
    '''
    def __init__(self, *args, **kwargs):
        super(MakeFixture, self).__init__(build_once=True, lazy_init=False,
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


@test.testfunction
@test.testfunction(tag='Pass')
def simple_test1(fixtures):
    logger.log.display('simple-test running!')

@test.testfunction(fixtures=first_fixture)
@test.testfunction(fixtures=second_fixture)
def fixture_test1(fixtures):
    logger.log.trace('fixture_test1 recieved %s' % fixtures)
    assert 'first-target' in fixtures\
            or 'second-target' in fixtures

@test.testfunction(fixtures={0:fixture.Fixture('testfixture')})
def nonlazy_fixture_test(fixtures):
    assert fixtures[0].built

shared_obj = None
@test.testfunction
def simple_multitest_start1(fixtures):
    global shared_obj
    shared_obj = True

@test.testfunction
def simple_multitest_complete1(fixtures):
    test.assertTrue(shared_obj)

@test.testfunction(tag='Fail')
def simple_fail_test1(fixtures):
    test.assertTrue(False, 'This test was bound to fail')

@test.testfunction(tag='Skip')
def simple_skip_test1(fixtures):
    test.skip('Skip this test.')

def simple_testfunction1(fixtures):
    pass

testsuite = suite.TestSuite('Simple testsuite')
testsuite.append(test.TestFunction(simple_testfunction1))

print('running code in %s' % __name__)
