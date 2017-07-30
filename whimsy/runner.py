import os
import traceback

from config import config
from logger import log
from suite import TestSuite
import terminal
from tee import tee
import test
from test import TestCase
import _util
from result import ConsoleLogger, Outcome, test_results_output_path


class Runner(object):
    '''
    The default runner class used for running test suites and cases.
    '''
    def __init__(self, suites, result_loggers=tuple()):
        self.suites = suites
        if not result_loggers:
            result_loggers = (ConsoleLogger(),)
        self.result_loggers = tuple(result_loggers)

    def run(self):
        '''
        Run our entire collection of suites.
        '''
        for logger in self.result_loggers:
            print logger
            logger.begin_testing()

        log.info(terminal.separator())
        log.info("Building all non 'lazy_init' fixtures")

        failed_builds = self.setup_unbuilt(
                self.suites.iter_fixtures(),
                setup_lazy_init=False)

        if failed_builds:
            error_str = ''
            for fixture, error in failed_builds:
                error_str += 'Failed to build %s\n' % fixture
                error_str += '%s' % error
            log.warn('Error(s) while building non lazy_init fixtures.')
            log.warn(error_str)

        outcomes = {self.run_suite(suite) for suite in self.suites}
        for logger in self.result_loggers:
            logger.end_testing()
        return self._suite_outcome(outcomes)


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

    def run_suite(self, test_suite):
        '''
        Run all tests/suites. From the given test_suite.

        1. Run child testcases passing them their required fixtures.
           - (We don't setup since the test case might override the fixture)
           - Collect results as tests are performed.
        2. Handle teardown for all fixtures in the test_suite.
        '''
        for logger in self.result_loggers:
            logger.begin(test_suite)

        suite_iterator = enumerate(test_suite)

        outcomes = set()

        suite_timer = _util.Timer()
        suite_timer.start()
        for (idx, (testlist, testcase)) in suite_iterator:
            assert isinstance(testcase, TestCase)
            outcome = self.run_test(testcase, fixtures=test_suite.fixtures)
            outcomes.add(outcome)

            # If there was a chance we might need to skip the remaining
            # tests...
            if outcome in Outcome.failfast \
                    and idx < len(test_suite) - 1:
                if config.fail_fast:
                    log.bold('Test failed with the --fail-fast flag provided.')
                    log.bold('Ignoring remaining tests.')
                    break
                if testlist.fail_fast or test_suite.fail_fast:
                    log.bold('Test failed in a fail_fast collection. Skipping'
                            ' remaining tests.')
                    self._generate_skips(testcase.name, suite_iterator)

        for fixture in test_suite.fixtures.values():
            fixture.teardown()
        suite_timer.stop()

        outcome = self._suite_outcome(outcomes)
        self._log_outcome(outcome, runtime=suite_timer.runtime())
        for logger in self.result_loggers:
            logger.end_current()

        return outcome

    def _suite_outcome(self, outcomes):
        '''
        A test suite can have the following results, they occur with the
        following priority/ordering.

        ERROR - Indicates that some error happened outside of a test case,
        likely in fixture setup.

        FAIL - Indicates that one or more tests failed.

        SKIP - Indicates that all contained tests and test suites were
        skipped.

        PASS - Indicates that all tests passed or EXFAIL'd
        '''
        if Outcome.ERROR in outcomes:
            return Outcome.ERROR
        elif Outcome.FAIL in outcomes:
            return Outcome.FAIL
        elif len(outcomes - {Outcome.PASS}):
            return Outcome.SKIP
        else:
            return Outcome.PASS

    def run_test(self, testobj, fixtures=None):
        '''
        Run the given test.

        This performs the bulkwork of the testing framework.
        1. Handle setup for all fixtures required for the specific test.
        2. Run the test.
        3. Teardown the fixtures for the test which are tied locally to the
           test.
        '''
        outdir = test_results_output_path(testobj)
        _util.mkdir_p(outdir)
        fstdout_name = os.path.join(outdir, config.constants.system_err_name)
        fstderr_name = os.path.join(outdir, config.constants.system_out_name)

        # Capture the output into a file.
        with tee(fstderr_name, stderr=True, stdout=False),\
                tee(fstdout_name, stderr=False, stdout=True):
            self._run_test(testobj, fstdout_name, fstderr_name, fixtures)

    def _run_test(self, testobj, fstdout_name, fstderr_name, fixtures):
        if fixtures is None:
            fixtures = {}

        outcome = None
        reason = None

        # We'll use a local shallow copy of fixtures to make it easier to
        # cleanup and override suite level fixtures with testcase level ones.
        fixtures = fixtures.copy()
        fixtures.update(testobj.fixtures)


        test_timer = _util.Timer()
        test_timer.start()

        for logger in self.result_loggers:
            logger.begin(testobj)

        def _run_test():
            try:
                testobj(fixtures=fixtures)
            except AssertionError as e:
                reason = e.message
                if not reason:
                    reason = traceback.format_exc()
                outcome = Outcome.FAIL
            except test.TestSkipException as e:
                reason = e.message
                outcome = Outcome.SKIP
            except test.TestFailException as e:
                reason = e.message
                outcome = Outcome.FAIL
            except Exception as e:
                reason = traceback.format_exc()
                outcome = Outcome.FAIL
            else:
                outcome = Outcome.PASS

            return outcome

        # Build any fixtures that haven't been built yet.
        log.debug('Building fixtures for TestCase: %s' % testobj.name)
        failed_builds = self.setup_unbuilt(
                fixtures.values(),
                setup_lazy_init=True)

        if failed_builds:
            reason = ''
            for fixture, error in failed_builds:
                reason += 'Failed to build %s\n' % fixture
                reason += '%s' % error
            reason = reason
            outcome = Outcome.ERROR
        else:
            outcome = _run_test()

        for fixture in testobj.fixtures.values():
            fixture.teardown()

        test_timer.stop()
        self._log_outcome(
                outcome,
                reason=reason,
                runtime=test_timer.runtime(),
                fstdout_name=fstdout_name,
                fstderr_name=fstderr_name)

        for logger in self.result_loggers:
            logger.end_current()

        return outcome

    def _generate_skips(self, failed_test, remaining_iterator):
        '''
        Generate SKIP for all remaining tests (for use with the failfast
        suite option)
        '''
        for (idx, (testlist, testcase)) in remaining_iterator:
            if isinstance(testcase, TestCase):
                reason = ("Previous test '%s' failed in a failfast"
                        " TestSuite." % failed_test)
                for logger in self.result_loggers:
                    logger.skip(testcase, reason)
            elif __debug__:
                raise AssertionError(_util.unexpected_item_msg)

    def _log_outcome(self, outcome, **kwargs):
        for logger in self.result_loggers:
            logger.set_current_outcome(outcome, **kwargs)

    def setup_unbuilt(self, fixtures, setup_lazy_init=False):
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

