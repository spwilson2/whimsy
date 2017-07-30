import abc
import collections
import time
import xml.etree.ElementTree as ET
import string
import functools
import pickle
import os

import _util
import terminal
import terminal as termcap
from config import constants, config
from test import TestCase
from suite import TestSuite
from logger import log

class InvalidResultException(Exception):
    pass

Outcome = _util.Enum(
    [
    'PASS',   # The test passed successfully.
    'XFAIL',  # The test ran and failed as expected.
    'SKIP',   # The test was skipped.
    'ERROR',  # There was an error during the setup of the test.
    'FAIL',   # The test failed to pass.
    ],
)
Result = Outcome

# Add all result enums to this module's namespace.
for result in Outcome.enums:
    globals()[str(result)] = result

Outcome.failfast = {ERROR, FAIL}

def test_results_output_path(test_case):
    return os.path.join(
            config.result_path, test_case.uid.replace('/','-'))

class ResultLogger(object):
    '''
    Interface which allows writing of streaming results to a file stream.
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def begin_testing(self):
        '''
        Signal the beginning of writing to the file stream. Indicates that
        results are about to be logged.
        '''
        pass

    @abc.abstractmethod
    def begin(self, item):
        '''
        Signal the beginning of the given item.
        '''
        pass


    @abc.abstractmethod
    def skip(self, item, **kwargs):
        '''Signal we are forcefully skipping the item due to some circumstance.'''

    @abc.abstractmethod
    def set_current_outcome(self, outcome, **kwargs):
        '''Set the outcome of the current item.'''

    @abc.abstractmethod
    def end_current(self):
        '''
        Signal the end of the current item.
        '''
        pass

    @abc.abstractmethod
    def end_testing(self):
        '''
        Signal the end of writing to the file stream. Indicates that
        results are done being logged.
        '''
        pass

    def __del__(self):
        self.end_testing()

class ConsoleLogger(ResultLogger):

    color = terminal.get_termcap()
    reset = color.Normal
    colormap = {
            FAIL: color.Red,
            ERROR: color.Red,
            PASS: color.Green,
            XFAIL: color.Cyan,
            SKIP: color.Cyan,
            }
    sep_fmtkey = 'separator'
    sep_fmtstr = '{%s}' % sep_fmtkey

    bad_item = ('Result formatter can only handle test cases'
            ' and test suites')

    def __init__(self):
        self.outcome_count = {outcome: 0 for outcome in Outcome.enums}
        self._item_list = []
        self._current_item = None
        self.timer = _util.Timer()

        self._started = False

    def begin_testing(self):
        self.timer.start()
        self._started = True

    def begin(self, item):
        '''
        Signal the beginning of the given item.
        '''
        if isinstance(item, TestSuite):
            self._begin_testsuite(item)
        elif isinstance(item, TestCase):
            self._begin_testcase(item)
        elif __debug__:
            raise AssertionError(self.bad_item)
        self._item_list.append(self._current_item)
        self._current_item = item

    def _begin_testsuite(self, test_suite):
        log.info('Starting TestSuite: %s' % test_suite.name)
    def _begin_testcase(self, test_case):
        log.info('Starting TestCase: %s' % test_case.name)

    def set_current_outcome(self, outcome, **kwargs):
        '''Set the outcome of the current item.'''
        if isinstance(self._current_item, TestSuite):
            pass # TODO, for now we dont' do anything with this.
        elif isinstance(self._current_item, TestCase):
            self._set_testcase_outcome(self._current_item, outcome, **kwargs)
        elif __debug__:
            raise AssertionError(self.bad_item)

    def _set_testcase_outcome(self, test_case, outcome, reason=None, **kwargs):
        log.bold(
                self.colormap[outcome]
                + test_case.name
                + self.reset)
        self.outcome_count[outcome] += 1

    def _set_testsuite_outcome(self, test_suite, outcome, **kwargs):
        pass

    # TODO: Change to force_set_outcome
    def skip(self, item, reason):
        '''Set the outcome of the current item.'''
        if isinstance(item, TestSuite):
            pass # TODO, for now we dont' do anything with this.
        elif isinstance(item, TestCase):
            self._skip_testcase(item, reason)
        elif __debug__:
            raise AssertionError(self.bad_item)

    def _skip_testcase(self, test_case, reason):
        log.display('{color}Skipping: {name}{reset}'.format(
            color=self.colormap[Outcome.SKIP],
            name=test_case.name,
            reset=self.reset))
        #log.display(reason)

    def end_current(self):
        if isinstance(self._current_item, TestSuite):
            self._end_testsuite(self._current_item)
        elif isinstance(self._current_item, TestCase):
            self._end_testcase(self._current_item)
        elif __debug__:
            raise AssertionError(self.bad_item)
        self._current_item = self._item_list.pop()

    def _end_testcase(self, test_case):
        pass
    def _end_testsuite(self, test_suite):
        pass

    def end_testing(self):
        if self._started:
            self.timer.stop()
            log.display(self._display_summary())
            self._started = False

    def _display_summary(self):
        most_severe_outcome = None
        outcome_fmt = ' {count} {outcome}'
        strings = []

        # Iterate over enums so they are in order of severity
        for outcome in Outcome.enums:
            count  = self.outcome_count[outcome]
            if count:
                strings.append(outcome_fmt.format(count=count, outcome=outcome.name))
                most_severe_outcome = outcome
        string = ','.join(strings)
        if most_severe_outcome is None:
            string = ' No testing done'
            most_severe_outcome = Outcome.PASS
        string += ' in {time:.2} seconds '.format(time=self.timer.runtime())

        return termcap.insert_separator(
                string,
                color=self.colormap[most_severe_outcome] + self.color.Bold)

class TestResult(object):
    def __init__(self, testitem, outcome, reason=None):
        self.name = testitem.name
        self.uid = testitem.uid
        self.outcome = outcome
        # NOTE: For now we don't care to keep the reason saved since we only
        # will care about outcomes.
        #self.reason = reason
class TestCaseResult(TestResult):
    def __init__(self, testitem, outcome, fstdout_name,
                 fstderr_name, *args, **kwargs):
        self.fstdout_name = fstdout_name
        self.fstderr_name = fstderr_name
        super(TestCaseResult, self).__init__(testitem, outcome,
                                             *args, **kwargs)
class TestSuiteResult(TestResult):
    pass

class InternalLogger(ResultLogger):
    def __init__(self, filestream):
        self._item_list = []
        self._current_item = None
        self.timer = _util.Timer()
        self.filestream = filestream
        self.results = []

    def _write(self, obj):
        print 'writing file'
        pickle.dump(obj, self.filestream)

    def begin_testing(self):
        print 'Started running internal logger'
        self.timer.start()

    def begin(self, item):
        self._item_list.append(self._current_item)
        self._current_item = item

    def skip(self, item, **kwargs):
        if isinstance(self._current_item, TestSuite):
            result_class = TestSuiteResult
        elif isinstance(self._current_item, TestCase):
            result_class = TestCaseResult
        elif __debug__:
            raise AssertionError(self.bad_item)
        result = result_class(self._current_item, Outcome.SKIP, **kwargs)
        self._write(result)
        self.results.append(result)

    def set_current_outcome(self, outcome, **kwargs):
        '''Set the outcome of the current item.'''
        if isinstance(self._current_item, TestSuite):
            result_class = TestSuiteResult
        elif isinstance(self._current_item, TestCase):
            result_class = TestCaseResult
        elif __debug__:
            raise AssertionError(self.bad_item)
        result = result_class(self._current_item, outcome, **kwargs)
        self._write(result)
        self.results.append(result)

    def end_current(self):
        self._current_item = self._item_list.pop()

    def end_testing(self):
        pass

    def load(self, filename):
        '''Load results out of a dumped file replacing our own results.'''
        self.results = []
        with open(filename, 'r') as picklefile:
            while True:
                pickle.load(picklefile)

class JUnitLogger(InternalLogger):
    # We use an internal logger to stream the output into a format we can
    # retrieve at the end and then format it into JUnit.
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>'

    def end_testing(self):
        '''
        Signal the end of writing to the file stream. Indicates that
        results are done being logged.
        '''
        JUnitFormatter()

class JUnitFormatter(object):
    '''
    Formats TestResults into the JUnit XML format.
    '''
    # Results considered passing under JUnit, we have a couple extra states
    # that aren't traditionally reported under JUnit.
    passing_results = {PASS, XFAIL}

    def __init__(self, result, translate_names=True):
        self.result = result

        if translate_names:
            self.name_table = string.maketrans("/.", ".-",)
        else:
            self.name_table = string.maketrans("", "")

    def __str__(self):
        self.root = ET.Element("testsuites")

        results = self.result
        if self.flatten:
            results = JUnitFormatter.flatten_suites(results)

        ET.ElementTree(self.convert_testsuite(self.root,
                                              results,
                                              self.flatten))
        return ET.tostring(self.root)

    def convert_testcase(self, xtree, testcase):
        xtest = ET.SubElement(xtree, "testcase",
                               name=testcase.name,
                               time="%f" % testcase.runtime)

        if testcase.result in self.passing_results:
            xstate = PASS
        elif testcase.result == SKIP:
            xstate = ET.SubElement(x_test, "skipped")
        elif testcase.result == FAIL:
            xstate = ET.SubElement(x_test, "failure")
        elif testcase.result == ERROR:
            xstate = ET.SubElement(x_test, "error")
        else:
            assert False, "Unknown test state"

        if xstate is not PASS:
            #TODO: Add extra output to the text?
            #xstate.text = "\n".join(msg)
            # TODO: Use these subelements for text.
            #<system-out>
            #    I am stdout!
            #</system-out>
            #<system-err>
            #    I am stderr!
            #</system-err>
            pass

    def convert_testsuite(self, xtree, suite):
        ''''''
        errors = 0
        failures = 0
        skipped = 0

        xsuite = ET.SubElement(xtree, "testsuite",
                                name=suite.name.translate(self.name_table),
                                time="%f" % suite.runtime)

        # Iterate over the tests and suites held in the test suite.
        for testresult in suite:
            # If the element is a test case attach it as such
            self.convert_testcase(xsuite, testresult)

            # Check the return value to fill in metadata for our xsuite
            if result.outcome not in self.passing_results:
                if result.outcome == SKIP:
                    skipped += 1
                elif result.outcome == ERROR:
                    errors += 1
                elif result.outcome == FAIL:
                    failures += 1
                else:
                    assert False, "Unknown test state"

            xsuite.set("errors", str(errors))
            xsuite.set("failures", str(failures))
            xsuite.set("skipped", str(skipped))
            xsuite.set("tests", str(len(suite.results)))

    def dump(self, dumpfile):
        dumpfile.write(str(self))


if __name__ == '__main__':
    import suite
    suiteresult = TestSuiteResult('Test Suite')
    parentsuiteresult = TestSuiteResult('Parent Test Suite')
    parentsuiteresult.results.append(suiteresult)

    parentsuiteresult.timer.start()
    parentsuiteresult.timer.stop()
    suiteresult.timer.start()
    suiteresult.timer.stop()


    for _ in range(2):
        testcase = TestCaseResult('testcase', result=PASS)
        testcase.timer.start()
        testcase.timer.stop()
        suiteresult.results.append(testcase)

    #formatter = JUnitFormatter(parentsuiteresult, flatten=True)
    #print(formatter)
    formatter = ConsoleFormatter(parentsuiteresult)
    print(formatter)
