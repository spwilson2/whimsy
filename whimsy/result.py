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
    def skip(self, item, *args, **kwargs):
        '''Signal we are forcefully skipping the item due to some circumstance.'''

    @abc.abstractmethod
    def set_current_outcome(self, outcome, *args, **kwargs):
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

    def begin_testing(self):
        self.timer.start()
        pass

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

    def set_current_outcome(self, outcome, *args, **kwargs):
        '''Set the outcome of the current item.'''
        if isinstance(self._current_item, TestSuite):
            pass # TODO, for now we dont' do anything with this.
        elif isinstance(self._current_item, TestCase):
            self._set_testcase_outcome(self._current_item, outcome, *args, **kwargs)
        elif __debug__:
            raise AssertionError(self.bad_item)

    def _set_testcase_outcome(self, test_case, outcome, reason=None):
        log.bold(
                self.colormap[outcome]
                + test_case.name
                + self.reset)
        self.outcome_count[outcome] += 1

    def _set_testsuite_outcome(self, test_suite, outcome):
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
        self.timer.stop()
        log.display(self._display_summary())
        pass

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
        string += ' in {time:.2} seconds '.format(time=self.timer.runtime())

        return termcap.insert_separator(
                string,
                color=self.colormap[most_severe_outcome] + self.color.Bold)

class TestResult(object):
    def __init__(self, test_case, outcome, reason=None):
        self.name = test_case.name
        self.uid = test_case.uid
        self.reason = reason
        self.outcome = outcome

class InternalLogger(ResultLogger):
    def __init__(self, filestream):
        # TODO: We'll use an internal formatter to write streaming results to
        # a file, and then on completion write out the JUnit.
        self._item_list = []
        self._current_item = None
        self.timer = _util.Timer()
        self.filestream = filestream

    def _write(self, obj):
        pickle.dump(obj, self.filestream)

    def begin_testing(self):
        self.timer.start()

    def begin(self, item):
        self._item_list.append(self._current_item)
        self._current_item = item

    def skip(self, item, *args, **kwargs):
        self._write(TestResult(self._current_item, Outcome.SKIP, *args,
            **kwargs))

    def set_current_outcome(self, outcome, *args, **kwargs):
        '''Set the outcome of the current item.'''
        self._write(TestResult(self._current_item, outcome, *args, **kwargs))

    def end_current(self):
        self._current_item = self._item_list.pop()

    def end_testing(self):
        pass

class JUnitLogger(ResultLogger):
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>'

    def __init__(self, filestream):
        # TODO: We'll use an internal formatter to write streaming results to
        # a file, and then on completion write out the JUnit.
        self.filestream = open(filestream)
        self.log = self.filestream.write

    def begin_testing(self):
        self.log(self.xml_header)

    def begin(self, item):
        '''
        Signal the beginning of the given item.
        '''
        pass

    def skip(self, item, *args, **kwargs):
        '''Signal we are forcefully skipping the item due to some circumstance.'''

    def set_current_outcome(self, outcome, *args, **kwargs):
        '''Set the outcome of the current item.'''

    def end_current(self):
        '''
        Signal the end of the current item.
        '''
        pass

    def end_testing(self):
        '''
        Signal the end of writing to the file stream. Indicates that
        results are done being logged.
        '''
        pass

class JUnitFormatter(object):
    '''
    Formats TestResults into the JUnit XML format.
    '''

    # Results considered passing under JUnit, we have a couple extra states
    # that aren't traditionally reported under JUnit.
    passing_results = {PASS, XFAIL}

    def __init__(self,
                 result,
                 translate_names=True,
                 flatten=True):
        '''
        :param flatten: Flatten out heirarchical tests in order to fit the
        basic JUnit format (test suites traditionally cannot hold other test
        suites).
        '''
        self.result = result
        self.flatten = flatten

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

    @staticmethod
    def flatten_suites(toplevel_suite):
        '''
        JUnit doesn't officially have a concept of heirarchecal test suites as
        far as I can tell, so to fix this we group tests at their finest
        granularity. That is, test cases are grouped in the test suite that
        directly contains them, not a suite of a suite.

        :returns: A new toplevel_suite which contains flattened suites.
        '''

        def metadata_copy_suiteresult(suite):
            copy = TestSuiteResult(suite.name)
            copy.timer = suite.timer
            return copy

        def recurse_flatten(suite):
            # Iterate over items in the suite, if they are other suites, we need
            # to recurse and do the same.
            # If they are tests then pull them out and save them. We'll attach
            # them to us.
            flattened_suite = metadata_copy_suiteresult(suite)
            our_testcases = []
            flat_suites = []

            for result in suite:
                if isinstance(result, TestCaseResult):
                    our_testcases.append(result)
                else:
                    flat_suites.extend(recurse_flatten(result))

            if our_testcases:
                # If there were test cases held in this test suite, we should
                # reattach them to our new copy and place us in the top level
                # collection
                flattened_suite.results.extend(our_testcases)
                flat_suites.append(flattened_suite)

            return flat_suites

        # Just copy the name since we're going to update all the results.
        new_toplevel_suite = metadata_copy_suiteresult(toplevel_suite)
        flatted_results = recurse_flatten(toplevel_suite)
        if flatted_results:
            new_toplevel_suite.results.extend(flatted_results)

        return new_toplevel_suite

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


    def convert_testsuite(self, xtree, suite, _flatten=False):
        '''
        '''
        errors = 0
        failures = 0
        skipped = 0

        # Remove the topmost suite that is containing other suites.
        if _flatten:
            xsuite = xtree
            _flatten = False
        else:
            xsuite = ET.SubElement(xtree, "testsuite",
                                    name=suite.name.translate(self.name_table),
                                    time="%f" % suite.runtime)

        # Iterate over the tests and suites held in the test suite.
        for result in suite:
            # If the element is a test case attach it as such
            if isinstance(result, TestCaseResult):
                self.convert_testcase(xsuite, result)
            else:
                # Otherwise recurse
                self.convert_testsuite(xsuite, result, _flatten)

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

        if not _flatten:
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
