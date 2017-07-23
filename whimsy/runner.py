import tempfile
import sys
import logging
import traceback

import logger as logger
import test as test
import suite as suite
from result import Result, ConsoleFormatter, TestSuiteResult, TestCaseResult
import terminal as terminal

_unexpected_item_msg = \
        'Only TestSuites and TestCases should be contained in a TestSuite'

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
            results = TestSuiteResult(test_suite.name)

        for name, fixture in test_suite.fixtures.items():
            fixture.setup()

        # We'll use a local shallow copy of fixtures to make it easier to
        # cleanup and override local fixtures.
        fixtures = fixtures.copy()
        fixtures.update(test_suite.fixtures)

        suite_iterator = enumerate(test_suite)

        for (idx, item) in suite_iterator:
            logger.log.info(terminal.separator())

            if isinstance(item, suite.TestSuite):
                result = self.run_suite(item, fixtures=fixtures)
            elif isinstance(item, test.TestCase):
                result = self.run_test(item, fixtures=fixtures)
            else:
                assert False, _unexpected_item_msg

            # Add the result of the test or suite to our test_suite results.
            results.results.append(result)

            if test_suite.failfast \
                    and result.outcome in Result.failfast:
                logger.log.inform('Previous test failed in a failfast suite,'
                                  ' skipping remaining tests.')
                self._generate_skips(result.name, results, suite_iterator)
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
            result = TestCaseResult(test.name)

        for name, fixture in test.fixtures.items():
            fixture.setup()

        # We'll use a local shallow copy of fixtures to make it easier to
        # cleanup and override local fixtures.
        fixtures = fixtures.copy()
        fixtures.update(test.fixtures)

        logger.log.info('TestCase: %s' % test.name)
        result.timer.start()
        try:
            test.test(result=result, fixtures=fixtures)
        except AssertionError as e:
            result.reason = e.message
            if not result.reason:
                result.reason = traceback.format_exc()
            result.outcome = Result.FAIL
        except Exception as e:
            result.outcome = traceback.format_exc()
            result.outcome = Result.FAIL
        else:
            result.outcome = Result.PASS
        result.timer.stop()

        if result.reason:
            logger.log.debug('%s'%result.reason)
        logger.log.inform('{color}{name} - {result}{reset}'.format(
                name=result.name,
                result=result.outcome,
                color=ConsoleFormatter.result_colormap[result.outcome],
                reset=terminal.termcap.Normal))
        logger.log.info(terminal.insert_separator(' %s '%result.outcome,
                color=ConsoleFormatter.result_colormap[result.outcome]))

        for name in test.fixtures:
            fixtures[name].teardown()

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
                assert False, _unexpected_item_msg
            logger.log.info('Skipping: %s' % item.name)
            results.results.append(result)
