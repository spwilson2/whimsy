import tempfile
import sys
import logging
import traceback

from logger import log
import test as test
import suite as suite
from result import Result, ConsoleFormatter, TestSuiteResult, TestCaseResult
import terminal as terminal
from config import config
import helper
import _util


def setup_unbuilt(fixtures, setup_lazy_init=False):
    failures = []
    for fixture in fixtures:
        if not fixture.built:
            if fixture.lazy_init == setup_lazy_init:
                try:
                    fixture.setup()
                except Exception as e:
                    failures.append((fixture.name,
                                     traceback.format_exc()))
    return failures

class Runner(object):
    '''
    The default runner class used for running test suites and cases.
    '''
    def __init__(self, test_suite, fixtures=None):
        if fixtures is None:
            fixtures = {}
        self.fixtures = fixtures
        self.test_suite = test_suite

    def run(self):
        log.info(terminal.separator())
        log.info("Building all non 'lazy_init' fixtures")

        setup_unbuilt(self.test_suite.enumerate_fixtures(),
                      setup_lazy_init=False)
        log.info('Running Tests')
        results = self.run_suite(self.test_suite)
        log.info(terminal.separator())

        return results

    def run_suite(self, test_suite, results=None, fixtures=None):
        '''
        Run all tests/suites. From the given test_suite.

        1. Handle setup for all fixtures in the test_suite
        2. Run child tests and test_suites passing them their required
           fixtures.
           - Collect results as tests are performed.
        3. Handle teardown for all fixtures in the test_suite.
        '''
        if results is None:
            results = TestSuiteResult(test_suite.name)
        if fixtures is None:
            fixtures = {}

        # We'll use a local shallow copy of fixtures to make it easier to
        # cleanup and override local fixtures.
        fixtures = fixtures.copy()
        fixtures.update(test_suite.fixtures)
        log.warn('Running suite %s' % test_suite.name)

        suite_iterator = enumerate(test_suite)

        for (idx, item) in suite_iterator:
            log.info(terminal.separator())
            log.warn('Running item %s' %item)

            if isinstance(item, suite.TestSuite):
                result = self.run_suite(item, fixtures=fixtures)
            elif isinstance(item, test.TestCase):
                result = self.run_test(item, fixtures=fixtures)
            else:
                assert False, _util.unexpected_item_msg

            # Add the result of the test or suite to our test_suite results.
            results.results.append(result)

            # If there was a chance we might need to skip the remaining
            # tests...
            if result.outcome in Result.failfast \
                    and idx < len(test_suite) - 1:
                if test_suite.failfast:
                    log.bold('Test failed in a failfast suite,'
                             ' skipping remaining tests.')
                    self._generate_skips(result.name, results, suite_iterator)
                elif config.fail_fast:
                    log.bold('Test failed with the --fail-fast flag provided.')
                    log.bold('Ignoring remaining tests.')
                    self._generate_skips(result.name, results, suite_iterator)

        for fixture in test_suite.fixtures.values():
            fixture.teardown()

        return results

    def run_test(self, testobj, fixtures=None, result=None):
        '''
        Run the given test.

        This performs the bulkwork of the testing framework.
        1. Handle setup for all fixtures required for the specific test.
        2. Run the test.
        3. Teardown the fixtures for the test which are tied locally to the
           test?
        '''
        if fixtures is None:
            fixtures = {}
        if result is None:
            result = TestCaseResult(testobj.name)
        else:
            # If we are given a result. We'll be updating its outcome by
            # testing.
            result.outcome = None

        # We'll use a local shallow copy of fixtures to make it easier to
        # cleanup and override suite level fixtures with testcase level ones.
        fixtures = fixtures.copy()
        fixtures.update(testobj.fixtures)

        # Build any fixtures that haven't been built yet.
        log.debug('Building fixtures for TestCase: %s' % testobj.name)

        def _run_test():
            log.info('TestCase: %s' % testobj.name)
            result.timer.start()
            try:
                testobj.test(fixtures=fixtures)
            except AssertionError as e:
                result.reason = e.message
                if not result.reason:
                    result.reason = traceback.format_exc()
                result.outcome = Result.FAIL
            except test.TestSkipException as e:
                result.reason = e.message
                result.outcome = Result.SKIP
            except test.TestFailException as e:
                result.reason = e.message
                result.outcome = Result.FAIL
            except Exception as e:
                result.reason = traceback.format_exc()
                result.outcome = Result.FAIL
            else:
                result.outcome = Result.PASS
            result.timer.stop()

        failed_builds = setup_unbuilt(fixtures.values(), setup_lazy_init=True)
        if failed_builds:
            result.outcome = Result.ERROR
            reason = bytes('')
            for fixture, error in failed_builds:
                reason += b'Failed to build %s\n' % fixture
                reason += b'%s' % error
            result.reason = str(reason)
        else:
            _run_test()

        if result.reason:
            log.debug('%s'%result.reason)
        log.bold('{color}{name} - {result}{reset}'.format(
                name=result.name,
                result=result.outcome,
                color=ConsoleFormatter.result_colormap[result.outcome],
                reset=terminal.termcap.Normal))
        log.info(terminal.insert_separator(' %s '%result.outcome,
                color=ConsoleFormatter.result_colormap[result.outcome]))

        for fixture in testobj.fixtures.itervalues():
            fixture.teardown()

        return result

    def _generate_skips(self, failed_test, results, remaining_iterator):
        '''
        Generate SKIP for all remaining tests (for use with the failfast
        suite option)
        '''
        for (idx, item) in remaining_iterator:
            if isinstance(item, suite.TestSuite):
                result = TestSuiteResult(item.name)
            elif isinstance(item, test.TestCase):
                result = TestCaseResult(item.name)
                result.reason = ("Previous test '%s' failed in a failfast"
                        " TestSuite." % failed_test)
                result.outcome = Result.SKIP
            else:
                assert False, _util.unexpected_item_msg
            log.info('Skipping: %s' % item.name)
            results.results.append(result)
