import whimsy.test as test
import whimsy.fixture as fixture

import subprocess

class MakeFixture(fixture.Fixture):
    '''
    Fixture should wait until all make targets are collected and tests are
    about to be ran, then should invocate a single instance of make for all
    targets.
    '''
    def __init__(self, *args, **kwargs):
        super(MakeFixture, self).__init__(*args, **kwargs)

    def setup(self):
        pass

    def teardown(self):
        pass

make_fixture = MakeFixture(lazy_init=False)

class MakeTargetFixture(fixture.Fixture):
    def __init__(self, *args, **kwargs):
        super(MakeTargetFixture, self).__init__(*args, **kwargs)
        self._requires.append(make_fixture)




class SimpleTest(test.TestBase):
    fixtures = []
    def test(self, fixtures):
        pass
