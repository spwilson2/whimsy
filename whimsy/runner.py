import traceback

from config import config
from logger import log
from result import Result, ConsoleFormatter, TestSuiteResult, TestCaseResult
from result import TestResultContainer
from suite import TestSuite
import terminal
from test import TestCase
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
    def __init__(self, suites):
        self.suites = suites

    def run(self):
        '''
        Run our entire collection of suites.
        '''
        log.info(terminal.separator())
        log.info("Building all non 'lazy_init' fixtures")

        failed_builds = setup_unbuilt(self.suites.iter_fixtures(),
                                      setup_lazy_init=False)
        if failed_builds:
            error_str = ''
            for fixture, error in failed_builds:
                error_str += 'Failed to build %s\n' % fixture
                error_str += '%s' % error
            log.warn('Error(s) while building non lazy_init fixtures.')
            log.warn(error_str)

        results = [self.run_suite(suite) for suite in self.suites]
        return TestResultContainer(results)


    def run_uid(self, uid):
        '''
        Traverse our tree looking for the uid, if we can find it, we also
        want to enumerate the fixtures that that testcase will have.
        '''
        for testitem in _util.iter_recursively(self.suites, inorder=True):
            if testitem.uid == uid:
                break
        else:
            log.warn('No test found for uid %s' % uid)
            return

        test_container = TestResultContainer()
        if isinstance(testitem, TestSuite):
            test_container.append(self.run_suite(testitem))
        elif isinstance(testitem, TestCase):
            # We need to create a parent suite result to attach this
            # to.
            test_container.append(self.run_test(testitem))
        elif __debug__:
            raise AssertionError(_util.unexpected_item_msg)

        return test_container

        # Create a new runner object with the suite we've found/created.

    def run_suite(self, test_suite, results=None):
        '''
        Run all tests/suites. From the given test_suite.

        1. Run child testcases passing them their required fixtures.
           - (We don't setup since the test case might override the fixture)
           - Collect results as tests are performed.
        2. Handle teardown for all fixtures in the test_suite.
        '''
        if results is None:
            results = TestSuiteResult(test_suite)
        log.display('Running TestSuite %s' % test_suite.name)

        suite_iterator = enumerate(test_suite)

        results.timer.start()
        for (idx, (testlist, testcase)) in suite_iterator:
            assert isinstance(testcase, TestCase)
            result = self.run_test(testcase, fixtures=test_suite.fixtures)
            results.append(result)

            # If there was a chance we might need to skip the remaining
            # tests...
            if result.outcome in Result.failfast \
                    and idx < len(test_suite) - 1:
                if testlist.fail_fast:
                    log.bold('Test failed with the --fail-fast flag provided.')
                    log.bold('Ignoring remaining tests.')
                    self._generate_skips(result.name, results, suite_iterator)
                elif test_suite.fail_fast:
                    log.bold('Test failed with the --fail-fast flag provided.')
                    log.bold('Ignoring remaining tests.')
                    self._generate_skips(result.name, results, suite_iterator)
                elif config.fail_fast:
                    log.bold('Test failed with the --fail-fast flag provided.')
                    log.bold('Ignoring remaining tests.')
                    self._generate_skips(result.name, results, suite_iterator)
        results.timer.stop()

        for fixture in test_suite.fixtures.values():
            fixture.teardown()

        return results

    def run_test(self, testobj, fixtures=None):
        '''
        Run the given test.

        This performs the bulkwork of the testing framework.
        1. Handle setup for all fixtures required for the specific test.
        2. Run the test.
        3. Teardown the fixtures for the test which are tied locally to the
           test.
        '''
        if fixtures is None:
            fixtures = {}

        # We'll use a local shallow copy of fixtures to make it easier to
        # cleanup and override suite level fixtures with testcase level ones.
        fixtures = fixtures.copy()
        fixtures.update(testobj.fixtures)

        result = TestCaseResult(testobj)
        def _run_test():
            log.info('TestCase: %s' % testobj.name)
            result.timer.start()
            try:
                testobj(fixtures=fixtures)
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

        # Build any fixtures that haven't been built yet.
        log.debug('Building fixtures for TestCase: %s' % testobj.name)
        failed_builds = setup_unbuilt(fixtures.values(), setup_lazy_init=True)
        if failed_builds:
            result.outcome = Result.ERROR
            reason = ''
            for fixture, error in failed_builds:
                reason += 'Failed to build %s\n' % fixture
                reason += '%s' % error
            result.reason = reason
        else:
            _run_test()

        if result.reason:
            log.debug('%s'%result.reason)
        log.bold('{color}{name} - {result}{reset}'.format(
                name=result.name,
                result=result.outcome,
                color=ConsoleFormatter.result_colormap[result.outcome],
                reset=terminal.termcap.Normal))

        for fixture in testobj.fixtures.values():
            fixture.teardown()

        return result

    def _generate_skips(self, failed_test, results, remaining_iterator):
        '''
        Generate SKIP for all remaining tests (for use with the failfast
        suite option)
        '''
        for (idx, (testlist, testcase)) in remaining_iterator:
            if isinstance(testcase, TestCase):
                result = TestCaseResult(testcase)
                result.reason = ("Previous test '%s' failed in a failfast"
                        " TestSuite." % failed_test)
                result.outcome = Result.SKIP
                result.timer.start()
                result.timer.stop()
            elif __debug__:
                raise AssertionError(_util.unexpected_item_msg)
            log.info('Skipping: %s' % testcase.name)
            results.results.append(result)
