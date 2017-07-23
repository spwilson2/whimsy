import imp
import os
import re
import traceback
import warnings

import test
import suite as suite_mod
import logger

default_filepath_regex = re.compile(r'((.+[-_]test)|(test[-_].+))\.py$')

def default_filepath_filter(filepath):
    filepath = os.path.basename(filepath)
    return True if default_filepath_regex.match(filepath) else False


teststring = 'TESTS'
class TestLoader(object):
    '''
    Base class for discovering tests.

    If tests are not tagged, automatically places them into their own test
    suite.
    '''
    teststring = teststring
    def __init__(self, suite=None, filepath_filter=default_filepath_filter):

        if suite is None:
            suite = suite_mod.TestSuite('Default Suite Collection',
                                        failfast=False)
        self._suite = suite
        self.filepath_filter = filepath_filter

        if __debug__:
            # Used to check if we have ran load_file to make sure we have
            # actually tried to load a file into our suite.
            self._loaded_a_file = False

    @property
    def suite(self):
        assert self._loaded_a_file
        return self._suite

    def enumerate_fixtures(self):
        pass

    def discover_files(self, root):
        files = []

        # Will probably want to order this traversal.
        for root, dirnames, filenames in os.walk(root):
            dirnames.sort()
            filenames.sort()
            filepaths = [os.path.join(root, filename) for filename in filenames]
            filepaths = filter(self.filepath_filter, filepaths)
            files.extend(filepaths)
        return files

    def load_file(self, path):
        '''
        Loads the given path for tests collecting suites and tests and placing
        them into the top_level_suite.
        '''
        # NOTE: There isn't a way to prevent reloading of test modules that are
        # imported by other test modules. It's up to users to never import
        # a test module.
        #
        # The implication for this is that we can't use a simple class variable
        # to keep track of instances of tests with __init__. If they were to
        # import a place where tests were defined then we would accidentally
        # enumerate those tests. So instead we require users to create
        # a variable 'TESTS' in each test file.
        if __debug__:
            self._loaded_a_file = True

        newdict = {'__builtins__':__builtins__}
        try:
            execfile(path, newdict, newdict)
        except Exception as e:
            logger.log.warn('Tried to load tests from %s but failed with an'
                    ' exception.' % path)
            logger.log.debug(traceback.format_exc())

        new_tests = newdict.get(self.teststring, None)
        if new_tests is not None:
            logger.log.debug('Discovered %d tests in %s' % (len(new_tests), path))
            self._suite.add_items(*new_tests)
        else:
            logger.log.warn('No tests discovered in %s' % path)
