import imp
import os
import re
import warnings

import whimsy.test as test
import whimsy.suite as suite

default_filepath_regex = re.compile(r'.*[-_]test.py$')

def default_filepath_filter(filepath):
    return True if default_filepath_regex.match(filepath) else False


class TestLoader(object):
    '''
    Base class for discovering tests.

    If tests are not tagged, automatically places them into their own test
    suite.
    '''
    def __init__(self, top_level_suite=None, filepath_filter=default_filepath_filter):

        if top_level_suite is None:
            top_level_suite = suite.TestSuite('Default Suite Collection')
        self.top_level_suite = top_level_suite

        self.filepath_filter = filepath_filter

    def discover_files(self, root):
        files = []

        # TODO: Will probably want to order this traversal.
        for root, dirnames, filenames in os.walk(root):
            filepaths = [os.path.join(root, filename) for filename in filenames]
            filepaths = filter(self.filepath_filter, filepaths)
            files.extend(filepaths)
        return files

    def load_file(self, path):
        '''
        Loads the given path for tests collecting suites and tests and placing
        them into the top_level_suite.
        '''
        # NOTE: There isn't a way to prevent reloading of test modules that
        # are imported by other test modules. It's up to users to never import
        # a test module.
        #
        # The implication for this is that we can't use a simple class
        # variable to keep track of instances of tests with __init__ if they
        # were to import a place were tests were defined. So instead we
        # require users to create a variable 'TESTS' in each test file.
        newdict = {'__builtins__':__builtins__}
        execfile(path, newdict, newdict)

        new_tests = newdict['TESTS']
        self.top_level_suite.add_items(*new_tests)
