'''
Built in test cases that verify particular details about a gem5 run.
'''
import difflib
import _util
import test
import os
import re

class Verifier(object):
    pass

_re_type = type(re.compile(''))

class MatchStdout(test.TestFunction):
    '''
    Compares a standard output to the test output and passes if they match,
    fails if they do not.
    '''
    def __init__(self, standard, ignore_regex=tuple()):
        '''
        :param standard: The path of the standard file to compare output to.
        '''
        super(MatchStdout, self).__init__(self.test, 'MatchStdout')
        self.standard = standard

        # Put the regex into an iterable.
        if isinstance(ignore_regex, _re_type) \
                or isinstance(ignore_regex, str):
            ignore_regex = (ignore_regex,)
        self.ignore_regex = ignore_regex

    def test(self, fixtures):
        # We need a tempdir fixture from our parent verifier suite.

        # TODO: Use constants.
        tempdir = fixtures['tempdir'].path
        test_stdout = os.path.join(tempdir, 'simout')
        diff = _util.diff_out_file(self.standard, test_stdout,
                                   self.ignore_regex)
        if diff is not None:
            test.fail('Stdout did not match:\n%s' % diff)
