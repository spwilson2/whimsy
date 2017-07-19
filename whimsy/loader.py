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
        old_tests = set(test.TestBase.list_all())
        # NOTE: There isn't a way to prevent reloading of test modules that
        # are imported by other test modules. It's up to users to never import
        # a test module.
        module = imp.load_source('test_file', path)

        #TODO: Collect test suites as well as just tests.

        new_tests = set(test.TestBase.list_all()) - old_tests
        self.top_level_suite.add_items(*new_tests)

