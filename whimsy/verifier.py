'''
Built in test cases that verify particular details about a gem5 run.
'''
import difflib
import _util
import test
import os
import re
from config import constants

class Verifier(test.TestFunction):
    tempdir_fixture_name = constants.tempdir_fixture_name

class MatchGoldStandard(test.TestFunction):
    '''
    Compares a standard output to the test output and passes if they match,
    fails if they do not.
    '''
    def __init__(self, standard_filename, name='MatchGoldStandard', ignore_regex=tuple(), test_filename='simout'):
        '''
        :param standard: The path of the standard file to compare output to.

        :param ignore_regex: A string, compiled regex, or iterable containing
        either which will be ignored in 'standard' and test output files when
        diffing.
        '''
        super(MatchGoldStandard, self).__init__(self.test, name)
        self.standard_filename = standard_filename
        self.test_filename = test_filename

        # Put the regex into an iterable.
        if isinstance(ignore_regex, _re_type) \
                or isinstance(ignore_regex, str):
            ignore_regex = (ignore_regex,)
        self.ignore_regex = ignore_regex

    def test(self, fixtures):
        # We need a tempdir fixture from our parent verifier suite.

        # Get the file from the tempdir of the test.
        tempdir = fixtures['tempdir'].path # TODO: Use constant.
        self.test_filename = os.path.join(tempdir, self.test_filename)

        diff = _util.diff_out_file(self.standard_filename,
                                   self.test_filename,
                                   self.ignore_regex)
        if diff is not None:
            test.fail('Stdout did not match:\n%s' % diff)

    def _generic_instance_warning(self, kwargs):
        '''
        Method for helper classes to tell users to use this more generic class
        if they are going to manually override the test_filename param.
        '''
        if 'test_filename' in kwargs:
            raise ValueError('If you are setting test_filename use the more'
                             ' generic %s instead' % MatchGoldStandard.__name__)

class MatchStdout(MatchGoldStandard):
    __file = constants.gem5_simulation_stdout
    def __init__(self, standard_filename, ignore_regex=tuple()):
        super(MatchStdout, self).__init__(standard_filename,
                                          test_filename=self.__file,
                                          name=MatchStdout.__name__,
                                          ignore_regex=ignore_regex)

class MatchStderr(MatchGoldStandard):
    __file = constants.gem5_simulation_stderr
    def __init__(self, standard_filename, ignore_regex=tuple()):
        super(MatchStderr, self).__init__(standard_filename,
                                          test_filename=self.__file,
                                          name=MatchStderr.__name__,
                                          ignore_regex=ignore_regex)

class MatchStats(MatchGoldStandard):
    __file = constants.gem5_simulation_stats
    def __init__(self, *args, **kwargs):
        self._generic_instance_warning(kwargs)
        super(MatchStats, self).__init__(standard_filename,
                                         test_filename=self.__file,
                                          name=MatchStats.__name__,
                                          ignore_regex=ignore_regex)

_re_type = type(re.compile(''))
