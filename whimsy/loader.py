import imp
import os
import re
import traceback
import warnings

from test import TestCase
import suite as suite_mod
import logger
import helper

# Ignores filenames that begin with '.'
# Will match filenames that either begin or end with 'test' or tests and use
# - or _ to separate additional name components.
default_filepath_regex = re.compile(r'(([^\.]+[-_]tests?)|(tests?[-_].+))\.py$')

def default_filepath_filter(filepath):
    filepath = os.path.basename(filepath)
    return True if default_filepath_regex.match(filepath) else False

def path_as_modulename(filepath):
    '''Return the given filepath as a module name.'''
    # Remove the file extention .py
    return os.path.splitext(os.path.basename(filepath))[0]


def path_as_testsuite(filepath, *args, **kwargs):
    '''
    Return the given filepath as a testsuite.

    The testsuite will be named after the containing directory of the file.
    '''
    suite_mod.TestSuite(
            os.path.split(os.path.dirname(os.path.abspath(filepath)))[-1],
            *args, **kwargs)

def _assert_files_in_same_dir(files):
    if files:
        directory = os.path.dirname(files[0])
        for f in files:
            assert os.path.dirname(f) == directory


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

        self.discovered_tests = helper.OrderedSet()

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
            if filenames:
                filenames.sort()
                filepaths = [os.path.join(root, filename) for filename in filenames]
                filepaths = filter(self.filepath_filter, filepaths)
                if filepaths:
                    files.append(filepaths)
        return files

    def load_root(self, root):
        '''
        Start from the given root loading files. Files in the same directory
        will be contained in the same TestSuite.
        '''
        for directory in self.discover_files(root):
            print(directory)
            if directory:

                if __debug__:
                    _assert_files_in_same_dir(directory)

                # Just use the pathname of the first file in the directory, they
                # all should have the same dirname.
                testsuite = path_as_testsuite(directory[0])
                for f in directory:
                    self.load_file(f)

    def load_file(self, path, testsuite=None):
        '''
        Loads the given path for tests collecting suites and tests and placing
        them into the top_level_suite.
        '''
        # NOTE: There isn't a way to prevent reloading of test modules that are
        # imported by other test modules. It's up to users to never import
        # a test module from a test module, otherwise those tests will be
        # enumerated twice.
        if __debug__:
            self._loaded_a_file = True

        if testsuite is None:
            testsuite = self._suite

        newdict = {
                '__builtins__':__builtins__,
                '__name__': path_as_modulename(path),
        }

        try:
            execfile(path, newdict, newdict)
        except Exception as e:
            logger.log.warn('Tried to load tests from %s but failed with an'
                    ' exception.' % path)
            logger.log.debug(traceback.format_exc())

        new_tests = TestCase.instances() - self.discovered_tests
        self.discovered_tests.update(new_tests)
        if new_tests is not None:
            logger.log.debug('Discovered %d tests in %s' % (len(new_tests), path))
            testsuite.add_items(*new_tests)
        else:
            logger.log.warn('No tests discovered in %s' % path)
