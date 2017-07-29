import abc
import collections
import time
import xml.etree.ElementTree as ET
import string
import functools
import pickle

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

    def __del__(self):
        self.end_testing()

class TestResult(object):
    '''
    Base Test Result class, acts as an ABC for TestResults. Can't be
    instantiated, but __init__ should be called by subclasses.
    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        '''
        :var timer: A timer used for timing the Test.
        :var result: The Result value of the Test.
        '''
        self.timer = _util.Timer()
        self._name = name
        # I want to be able to store all output from the test in this.
        #
        # Subclasses, such as a gem5 test result might contain more results,
        # but it's up to them to concatinate them into standard formats.

    @abc.abstractproperty
    def outcome():
        '''Should return the result of the TestResult.'''
        pass

    @property
    def runtime(self):
        return self.timer.runtime()

    @property
    def name():
        return self._name

class SubtestResult(TestResult):
    '''
    Holds information corresponding to a single test case result.
    '''
    def __init__(self, testcase, outcome=None, reason=None):
        super(SubtestResult, self).__init__(testcase.name)
        assert isinstance(testcase, Subtest)
        self.uid = testcase.uid

        self._outcome = outcome

    @property
    def outcome(self):
        return self._outcome

    @outcome.setter
    def outcome(self, val):
        self._outcome = val

    @property
    def name(self):
        return self._name

class TestCaseResult(TestResult):
    '''
    Holds information corresponding to a single test case result.
    '''
    def __init__(self, testcase, outcome=None, reason=None):
        super(TestCaseResult, self).__init__(testcase.name)
        assert isinstance(testcase, TestCase)
        self.uid = testcase.uid

        self._outcome = outcome
        # TODO maybe?
        #self.fstdout = fstdout
        #self.fstderr = fstderr
        self.reason = reason

    @property
    def outcome(self):
        return self._outcome

    @outcome.setter
    def outcome(self, val):
        self._outcome = val

    @property
    def name(self):
        return self._name


class TestResultContainer(list):
    def __add__(self, rhs):
        return TestResultContainer(list.__add__(self, rhs))

    @property
    def outcome(self):
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

        for result in self.results:
            if result.outcome == ERROR:
                return ERROR
            if result.outcome  != SKIP:
                all_skipped = False
            if result.outcome  == FAIL:
                failed = True

        if failed:
            return FAIL
        if all_skipped:
            return SKIP
        return PASS

    def iter_inorder(self):
        '''
        Iterate over all the testsuite results and testcase results contained
        in this collection of results. Traverses the tree in in-order fashion.
        '''
        return _util.iter_recursively(self, inorder=True)

    def iter_leaves(self):
        '''
        Recursively iterate over all the TestCaseResult's contained in this
        TestSuiteResult and TestSuiteResult's we contain.
        '''
        return _util.iter_recursively(self, inorder=False)

    def iter_self_contained(self):
        '''
        Iterate through all items that are self_contained.
        '''
        for item in self.iter_inorder():
            if getattr(item, 'self_contained', False):
                yield item

    @property
    def runtime(self):
        time = 0
        for testresult in self:
            time += testresult.runtime
        return time


class TestSuiteResult(TestResultContainer, TestResult):
    '''
    Holds information containing one or more test cases or suites.
    '''
    def __init__(self, testsuite):
        # Explicityly bypass python MRO
        TestResult.__init__(self, testsuite.name)
        assert isinstance(testsuite, TestSuite)
        #self.runtime = testsuite.runtime
        self.uid = testsuite.uid
        self.results = []

    @property
    def name(self):
        return self._name

class ResultFormatter(object):
    '''
    Formats TestResults into a specific output.
    '''
    __metaclass__ = abc.ABCMeta
    def __init__(self, result):
        self.result = result

    @abc.abstractmethod
    def dump(self, dumpfile):
        '''Dumps the result to the given dumpfile'''

class ConsoleFormatter(ResultFormatter):
    '''
    Formats results for a console.
    '''
    color = termcap.get_termcap()
    reset = color.Normal
    result_colormap = {
        FAIL: color.Red,
        ERROR: color.Red,
        PASS: color.Green,
        XFAIL: color.Cyan,
        SKIP: color.Cyan,
    }
    sep_fmtkey = 'separator'
    sep_fmtstr = '{%s}' % sep_fmtkey
    verbosity_levels = _util.Enum([
            'FATAL',
            'INFO',
            'DEBUG',])

    def __init__(self, result, verbosity=verbosity_levels.INFO,
                 only_testcases=True,
                 only_failed=config.list_only_failed):
        super(ConsoleFormatter, self).__init__(result)
        self.only_testcases = only_testcases
        self.verbosity = verbosity
        self.only_failed = only_failed

    def format_test(self, test):
        string = ''
        if (not self.only_failed) or test.outcome == FAIL:
            string += '{color}{result}: {name}{reset}\n'.format(
                    color=self.result_colormap[test.outcome],
                    result=test.outcome,
                    name=test.name,
                    reset=self.reset)
            if self.verbosity > self.verbosity_levels.DEBUG:
                if test.reason:
                    string += 'Reason:\n\n'
                    string += '%s\n\n' % test.reason
        return string

    def format_tests(self, suite):
        string = ''
        if self.only_failed:
            only_failed_string = 'Only printing failed tests.\n'
            string = only_failed_string
        for testcase in suite:
            string += self.format_test(testcase)

        if self.only_failed and string == only_failed_string:
            string += self.color.Bold + 'No tests failed.\n' + self.reset

        return string

    def format_summary(self, summary):
        result_heading = 'Result'
        count_heading = 'Count'
        h_sep = ' | '
        v_sep = '-'

        summary = {name:len(results) for name, results in summary.items() }

        # First get the alignment to start/stop numbers at.
        namestrings = map(str, Result.enums)
        namestrings.append(result_heading)
        maxname = max(map(len, namestrings))

        result_strings = map(str, summary.values())
        result_strings.append(count_heading)
        maxresult = max(map(len, result_strings))

        divider = '{:-%d}' % (maxname + maxresult + len(h_sep))
        summarystring = '{result: <{maxname}}{h_sep}{count: >{maxresult}}\n'.format(
                h_sep=h_sep,
                maxname=maxname,
                maxresult=maxresult,
                result=result_heading,
                count=count_heading)
        formatstring = '{name: <{maxname}}{h_sep}{count: >{maxresult}}\n'

        # Actually start building our string now.
        string = summarystring
        string += len(summarystring) * '-' + '\n'
        # Iterate through the results in the specified order by the enum type.
        for key in Result.enums:
            string += formatstring.format(
                    h_sep=h_sep,
                    name=key,
                    count=summary[key],
                    maxname=maxname,
                    maxresult=maxresult)
        return string

    def summarize_results(self):
        # If only_testcases don't summarize information about suites.
        summary = {enum:[] for enum in Result.enums}
        if self.only_testcases:
            for test in self.result.iter_leaves():
                summary[test.outcome].append(test)
        return summary

    def format_separators(self, string):
        (termw, termh) = termcap.terminal_size()
        format_separators = {self.sep_fmtkey: '='*termw}
        return string.format(**format_separators)

    def format_efficient_summary(self, summarized_results):
        fmt = ' {count} {outcome} in {time:.2} seconds '

        # Outcomes should be ordered from lowest severity to highest.
        for outcome in range(len(Result.enums)-1, -1, -1):
            outcome = Result.enums[outcome]
            if summarized_results[outcome]:
                fmt = fmt.format(count=len(summarized_results[outcome]),
                                 outcome=str(outcome),
                                 time=self.result.runtime)
                return termcap.insert_separator(
                        fmt,
                        color=self.result_colormap[outcome] + self.color.Bold)

        return self.sep_fmtstr


    def __str__(self):
        string = self.sep_fmtstr
        # If we only care about printing test cases logic looks simpler.
        if self.only_testcases:
            string += self.format_tests(self.result.iter_leaves())

        if not self.only_failed:
            # Create separator between previous results.
            if self.only_testcases:
                string += self.sep_fmtstr
            string += self.format_summary(self.summarize_results())

        # The final format separator contains the efficient summary.
        string += self.format_efficient_summary(self.summarize_results())

        return self.format_separators(string)

    def dump(self, dumpfile):
        dumpfile.write(str(self))

class InternalFormatter(ResultFormatter):
    '''
    Result formatter for internal use by this library.

    This result formatter can be used to save results in order to rerun failed
    tests.
    '''
    def __init__(self, arg=None, fromfile=False):
        '''
        :param fromfile: Indicates that the first argument is a file where
        previous results were dumped and that we should parse results form
        that file.
        '''
        super(InternalFormatter, self).__init__(arg)
        if fromfile:
            with open(arg, 'r') as f:
                self.undump(f)

    def __str__(self):
        return pickle.dumps(self.result, protocol=constants.pickle_protocol)

    def dump(self, dumpfile):
        pickle.dump(self.result, dumpfile, protocol=constants.pickle_protocol)

    def undump(self, dumpfile):
        self.result = pickle.load(dumpfile)

class JUnitFormatter(ResultFormatter):
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
        super(JUnitFormatter, self).__init__(result)
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
