import whimsy.test as test
import whimsy.suite as suite
import whimsy.result as result

class Runner(object):
    '''
    The default runner class used for running test suites and cases.
    '''

    def run_suite(self, test_suite, results=None, fixtures={}):
        '''
        Run all tests/suites. From the given test_suite.

        1. Handle setup for all fixtures in the test_suite
        2. Run child tests and test_suites passing them their required
           fixtures.
           - Collect results as tests are performed.
        3. Handle teardown for all fixtures in the test_suite.
        '''
        if results is None:
            results = result.Result()

        for name, fixture in test_suite.fixtures.items():
            fixture.setup()

        # We'll use a local shallow copy of fixtures to make it easier to
        # cleanup and override local fixtures.
        fixtures = fixtures.copy()
        fixtures.update(test_suite.fixtures)

        # TODO: Collect results
        for item in test_suite:

            if isinstance(item, suite.TestSuite):
                self.run_suite(item, results, fixtures)
            elif isinstance(item, test.TestCase):
                self.run_test(item, results, fixtures)
            else:
                assert(False)

            print(item)
            print(fixtures)
            print(results)

        for fixture in test_suite.fixtures.values():
            fixture.teardown()

    def run_test(self, test, results=None, fixtures={}):
        '''
        Run the given test.

        This performs the bulkwork of the testing framework.
        1. Handle setup for all fixtures required for the specific test.
        2. Run the test.
        3. Teardown the fixtures for the test which are tied locally to the
           test?
        '''

        if results is None:
            results = result.Result()

        for name, fixture in test.fixtures.items():
            fixture.setup()

        # We'll use a local shallow copy of fixtures to make it easier to
        # cleanup and override local fixtures.
        fixtures = fixtures.copy()
        fixtures.update(test.fixtures)

        print('About to run test')
        test.test(fixtures=fixtures)

        for name in test.fixtures:
            #import pdb; pdb.set_trace()
            fixtures[name].teardown()
