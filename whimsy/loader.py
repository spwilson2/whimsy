import imp
import os
import re

import whimsy.test as test

default_filepath_regex = re.compile(r'.*[-_]test.py$')

def default_filepath_filter(filepath):
    return True if default_filepath_regex.match(filepath) else False

class TestLoader(object):
    '''
    Base class for discovering tests.

    If tests are not tagged, automatically places them into their own test
    suite.
    '''
    def __init__(self, filepath_filter=default_filepath_filter):
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
        Loads the given path for tests.
        '''
        old_tests = set(test.TestBase.list_all())
        module = imp.load_source('testsource', path)
        new_tests = set(test.TestBase.list_all()) - old_tests
        print(new_tests)
