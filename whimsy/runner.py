import tempfile
import sys
import logging

import whimsy.logger as logger
import whimsy.test as test
import whimsy.suite as suite
import whimsy.result

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
            results = whimsy.result.TestSuiteResult()

        for name, fixture in test_suite.fixtures.items():
            fixture.setup()

        # We'll use a local shallow copy of fixtures to make it easier to
        # cleanup and override local fixtures.
        fixtures = fixtures.copy()
        fixtures.update(test_suite.fixtures)

        for item in test_suite:

            if isinstance(item, suite.TestSuite):
                result = self.run_suite(item, fixtures=fixtures)
            elif isinstance(item, test.TestCase):
                result = self.run_test(item, fixtures=fixtures)
            else:
                assert(False)

            # Add the result of the test or suite to our test_suite results.
            results.add_result(result)

            if test_suite.failfast \
                    and result.result in whimsy.result.Result.failfast:
                # TODO: Mark the rest of the items as skipped.
                break

        for fixture in test_suite.fixtures.values():
            fixture.teardown()

        return results

    def run_test(self, test, fixtures={}, result=None):
        '''
        Run the given test.

        This performs the bulkwork of the testing framework.
        1. Handle setup for all fixtures required for the specific test.
        2. Run the test.
        3. Teardown the fixtures for the test which are tied locally to the
           test?
        '''
        if result is None:
            result = whimsy.result.TestCaseResult()

        for name, fixture in test.fixtures.items():
            fixture.setup()

        # We'll use a local shallow copy of fixtures to make it easier to
        # cleanup and override local fixtures.
        fixtures = fixtures.copy()
        fixtures.update(test.fixtures)

        saved_stdout = sys.stdout
        saved_stderr = sys.stderr

        # Create a log to store the test output in.
        log = logging.getLogger(__name__)
        log.setLevel(logging.DEBUG)

        # Redirect log back to stdout so when we redirect it to the log we
        # still see it in the console.
        log.addHandler(logging.StreamHandler(saved_stdout))

        # Redirect stdout and stderr to logger for the test.
        sys.stdout = logger.StreamToLogger(log, logging.INFO)
        sys.stderr = logger.StreamToLogger(log, logging.WARN)


        result.timer.start()
        try:
            test.test(result=result, fixtures=fixtures)
        except:
            result.result = whimsy.result.Result.FAIL
        result.timer.stop()

        if result.result is None:
            result.result = whimsy.result.Result.PASS

        # Restore stdout and stderr
        sys.stdout = saved_stdout
        sys.stderr = saved_stderr

        for name in test.fixtures:
            fixtures[name].teardown()

        return result
