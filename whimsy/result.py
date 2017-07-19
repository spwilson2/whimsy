import abc
import time

import _util

class InvalidResultException(Exception):
    pass

Result = _util.Enum(
    {
    'PASS',   # The test passed successfully.
    'EXFAIL', # The test ran and failed as expected.
    'SKIP',   # The test was skipped.
    'FAIL',   # The test failed to pass.
    'ERROR',  # There was an error during the setup of the test.
    },
    namespace='Result'
)

Result.failfast = {Result.ERROR, Result.FAIL}

class TestResult(object):
    '''
    Base Test Result class, acts as an ABC for TestResults. Can't be
    instantiated, but __init__ should be called by subclasses.
    '''
    __metaclass__ = abc.ABCMeta
    def __init__(self):
        '''
        :var timer: A timer used for timing the Test.
        :var result: The Result value of the Test.
        '''
        self.timer = _util.Timer()
        # I want to be able to store all output from the test in this.
        #
        # Subclasses, such as a gem5 test result might contain more results,
        # but it's up to them to concatinate them into standard formats.

    @abc.abstractproperty
    def result():
        pass

class TestCaseResult(TestResult):
    '''
    Holds information corresponding to a single test case result.
    '''
    def __init__(self, *args, **kwargs):
        super(TestCaseResult, self).__init__(*args, **kwargs)
        self._result = None

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, val):
        self._result = val


class TestSuiteResult(TestResult):
    '''
    Holds information containing one or more test cases or suites.
    '''
    def __init__(self, *args, **kwargs):
        super(TestSuiteResult, self).__init__(*args, **kwargs)
        self._results = []

    @property
    def result(self):
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
        failed = False
        all_skipped = True

        for result in self._results:
            result = result.result
            if result == Result.ERROR:
                return Result.ERROR
            if result != Result.SKIP:
                all_skipped = False
            if result == Result.FAIL:
                failed = True

        if failed:
            return Result.FAIL
        if all_skipped:
            return Result.SKIP
        return Result.PASS

    def add_result(self, result):
        self._results.append(result)


class ResultFormatter(object):
    '''
    Formats TestResults into a specific output.
    '''
    __metaclass__ = abc.ABCMeta
    def __init__(self, result):
        pass


class JUnitFormatter(ResultFormatter):
    '''
    Formats TestResults into the JUnit XML format.
    '''
    def __init__(self, *args, **kwargs):
        super(JUnitFormatter, self).__init__(*args, **kwargs)
