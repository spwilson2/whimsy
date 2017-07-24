import imp
import os
import re
import traceback
import types
import warnings
import copy

from test import TestCase
from suite import TestSuite
from fixture import Fixture
import logger
import helper
import _util

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
    TestSuite(os.path.split(os.path.dirname(os.path.abspath(filepath)))[-1],
              *args, **kwargs)

def _assert_files_in_same_dir(files):
    if files:
        directory = os.path.dirname(files[0])
        for f in files:
            assert os.path.dirname(f) == directory


class TestLoader(object):
    '''
    Base class for discovering tests.

    If tests are not tagged, automatically places them into their own test
    suite.
    '''
    def __init__(self, filepath_filter=default_filepath_filter, tags=None):

        self._suite = TestSuite('Default Suite Collection',
                                failfast=False)
        self.filepath_filter = filepath_filter

        if __debug__:
            # Used to check if we have ran load_file to make sure we have
            # actually tried to load a file into our suite.
            self._loaded_a_file = False

        if tags is None:
            tags = set()
        if isinstance(tags, str):
            tags = (tags,)
        self.tags = tags
        print(self.tags)

        self._wrapped_classes = {}
        self._collected_test_items = helper.OrderedSet()
        self._collected_fixtures = helper.OrderedSet()

        self._fixtures = []
        self._suites = []
        self._tests = []

        self._cached_suitecall = None

    @property
    def tags(self):
        return tuple(self._tags)

    @tags.setter
    def tags(self, val):
        # Remove our cached called if tags is changed.
        self._cached_suitecall = None
        self._tags = set(val)

    @property
    def suites(self):
        assert self._loaded_a_file
        return tuple(*self._suites)

    @property
    def tests(self):
        assert self._loaded_a_file
        return tuple(*self._tests)

    @property
    def fixtures(self):
        assert self._loaded_a_file
        return tuple(*self._fixtures)

    @property
    def suite(self):
        '''
        Return a suite containing all tests/suites that are marked with all of our
        tags.

        NOTE: This is an expensive operation since we need to recurse the
        tree of suites to build tag indexes.
        '''
        assert self._loaded_a_file
        if not self.tags:
            return self._suite

        if self._cached_suitecall is not None:
            return self._cached_suitecall

        newsuite = copy.deepcopy(self._suite)
        if self._collect_with_tags(newsuite, set()):
            self._cached_suitecall = newsuite
        else:
            self._cached_suitecall = \
                TestSuite('Default Suite Collection',
                          failfast=False)
        return self._cached_suitecall

    def _collect_with_tags(self, suite, recursive_tags):
        '''
        Collect testsuites and testcases which have the given tags. Leaves the
        testsuite heirarchy intact if a parent suite does not have the given
        tags but at some level of he heirarchy a test or suite has the given
        tags.

        :param suite: The current level suite to search for tests/suites with
        self._tags

        :param recursive_tags: A recursively expanded variable which holds the
        tags of the current test suite plus those of all suites that hold us.

        NOTE: Right now suites are set up to be collected only if the test has
        ALL the tags in self._tags, that is if the test suite set of tags is
        a superset of the the tags in self._tags.
        '''
        # TODO: Discuss if should be issuperset or subset, or more than likely
        # should be a config option.
        kept_items = []
        for testitem in suite:
            if isinstance(testitem, TestCase):
                print('testitem is testscase')
                print(recursive_tags or testitem.tags)
                if (recursive_tags or testitem.tags).issuperset(self._tags):
                    kept_items.append(testitem)
            elif isinstance(testitem, TestSuite):
                suitetags = testitem.tags + recursive_tags
                if suitetags.issuperset(self._tags):
                    kept_items.append(testitem)
                else:
                    if self._collect_with_tags(testitem,
                                               testitem.tags or tags):
                        kept_items.append(testitem)
        if kept_items:
            suite.items = kept_items
        return bool(kept_items)


    def _build_tags(self, suite, itemtags, tags):
        '''
        Build an dictionary index of all TestSuite and TestCases stored in the
        given suite mapped to their tags.

        NOTE: Currently unused, likely will be used by some querying tools.
        '''
        for testitem in suite:
            if isinstance(testitem, TestCase):
                itemtags[testitem] = tags + test.tags
            elif isinstance(testitem, TestSuite):
                self._build_tags(testitem, itemtags, testitem.tags + tags)
            else:
                assert False, _util.unexpected_item_msg

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
        if __debug__:
            self._loaded_a_file = True

        for directory in self.discover_files(root):
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
        path = os.path.abspath(path)
        # NOTE: There isn't a way to prevent reloading of test modules that are
        # imported by other test modules. It's up to users to never import
        # a test module from a test module, otherwise those tests will be
        # enumerated twice.
        if __debug__:
            self._loaded_a_file = True

        # Remove our cache of tagged test items since they may be modified.
        self._cached_suitecall = None

        if testsuite is None:
            testsuite = self._suite

        newdict = {
                '__builtins__':__builtins__,
                '__name__': path_as_modulename(path),
                '__file__': path,
        }

        self._wrap_init(TestSuite, self._collected_test_items)
        self._wrap_init(TestCase, self._collected_test_items)
        self._wrap_init(Fixture, self._collected_fixtures)

        def cleanup():
            self._unwrap_init(TestSuite)
            self._unwrap_init(TestCase)
            self._unwrap_init(Fixture)
            self._collected_fixtures = helper.OrderedSet()
            self._collected_test_items = helper.OrderedSet()

        try:
            execfile(path, newdict, newdict)
        except Exception as e:
            logger.log.warn('Tried to load tests from %s but failed with an'
                    ' exception.' % path)
            logger.log.debug(traceback.format_exc())
            cleanup()
            return

        # Separate the instances so we can manipulate them more easily.
        # We also keep them together so we know ordering.
        test_items = self._collected_test_items
        testcases = []
        testsuites = []
        for item in test_items:
            if isinstance(item, TestCase):
                testcases.append(item)
            elif isinstance(item, TestSuite):
                testsuites.append(item)

        self._suites.extend(testsuites)
        self._tests.extend(testcases)
        self._fixtures.extend(self._collected_fixtures)

        if testcases:
            logger.log.debug('Discovered %d tests and %d testsuites in %s'
                             '' % (len(testcases), len(testsuites), path))
            if testsuites:
                # Remove all tests contained in testsuites from being attached
                # directly to this module's test suite.
                testcases = helper.OrderedSet(testcases)
                for testsuite in testsuites:
                    test_items -= helper.OrderedSet(testsuite.iter_leaves())
            self._suite.add_items(*testcases)
        elif testsuites:
            logger.log.warn('No tests discovered in %s, but found %d '
                            ' TestSuites' % (path, len(testsuites)))
        else:
            logger.log.warn('No tests discovered in %s' % path)

        cleanup()


    def _wrap_init(self, cls, collector):
        '''
        Wrap the given cls' __init__ method with a wrapper that will keep an
        OrderedSet of the instances.

        Note: If any other class monkey patches the __init__ method as well,
        this will lead to issues. Keep __debug__ mode enabled to ensure this
        never happens.
        '''
        assert cls not in self._wrapped_classes
        old_init = cls.__init__

        def instance_collect_wrapper(self, *args, **kwargs):
            collector.add(self)
            old_init(self, *args, **kwargs)

        our_wrapper = types.MethodType(instance_collect_wrapper, None, cls)
        if __debug__:
            self._wrapped_classes[cls] = (old_init, our_wrapper)
        else:
            self._wrapped_classes[cls] = old_init

        cls.__init__ = our_wrapper

    def _unwrap_init(self, cls):
        '''
        Unwrap the given cls' __init__ method.

        Note: If any other class monkey patches the __init__ method as well,
        this will lead to issues. Keep __debug__ mode enabled to ensure this
        never happens.
        '''
        if __debug__:
            (old_init, our_init) = self._wrapped_classes[cls]
            assert cls.__init__ == our_init, \
                    "%s's __init__ has changed, we can not restore it." % cls
        else:
            old_init = self._wrapped_classes[cls]

        cls.__init__ = old_init
        del self._wrapped_classes[cls]
