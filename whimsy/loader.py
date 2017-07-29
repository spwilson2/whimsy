import os
import re
import sys
import traceback
import types
import copy

import helper
from fixture import Fixture
from logger import log
from suite import TestSuite, SuiteList, TestList
from test import TestCase
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
    return TestSuite(os.path.split(helper.absdirpath(filepath))[-1],
        *args, **kwargs)

if __debug__:
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

        self._suites = SuiteList()
        self.filepath_filter = filepath_filter

        if __debug__:
            # Used to check if we have ran load_file to make sure we have
            # actually tried to load a file into our suite.
            self._loaded_a_file = False

        if tags is None:
            tags = set()
        if isinstance(tags, str):
            tags = (tags,)
        # NOTE: Purposely use the property version to drop cache
        self.tags = tags

        # List of all the fixtures we have collected.
        self._fixtures = []

        # Tests and suites are identified by the test loader in a format that
        # enforces uniqueness - both so users and the test system can identify
        # unique tests.
        # Reverse index: testitem->uid
        self._test_index  = _util.OrderedDict()
        self._suite_index = _util.OrderedDict()

        # Reverse index: uid->testitem NOTE: Currently unused.
        self._test_rindex = {}
        self._suite_rindex = {}

        # Holds a mapping of tag->testitem
        self._cached_tag_index = None
        # Holds a test suite which contains tests which have our self.tags
        self._cached_suitecall = None

        # Member variables used to keep track of instances of suites, cases,
        # and fixtures when execfile'ing.
        # They are temporary and will be reset for each file we load.
        self._wrapped_classes = {}
        self._collected_test_items = helper.OrderedSet()
        self._collected_fixtures = helper.OrderedSet()


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
        return self._suites

    @property
    def tests(self):
        assert self._loaded_a_file
        return tuple(self._test_rindex)

    @property
    def fixtures(self):
        assert self._loaded_a_file
        return tuple(self._fixtures)

    def collection_with_tags(self):
        '''
        Return a suite collection containing all tests/suites that are marked
        with all of our tags.

        NOTE: This is an expensive operation since we need to recurse the
        tree of suites to build tag indexes.
        '''
        assert self._loaded_a_file
        if not self.tags:
            return self._suites

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


    def tag_index(self, tag):
        '''
        Return a list of test items with the given tag.
        '''
        if self._cached_tag_index is None:
            item_to_tags = {}
            uniq_tags = set()
            self._build_tags(self._suite,
                             item_to_tags,
                             self._suite.tags.copy(),
                             uniq_tags)
            # Build Reverse the index of single tag to list of items
            self._cached_tag_index = {}
            for test, testtags in item_to_tags.iteritems():
                for _tag in uniq_tags:
                    if _tag in testtags:
                        testlist = self._cached_tag_index.setdefault(_tag,
                                                                     [])
                        testlist.append(test)

        return self._cached_tag_index.get(tag, [])

    def _build_tags(self, suite, itemtags, recursive_tags, uniq_tags):
        '''
        Build an dictionary index of all TestSuite and TestCases stored in the
        given suite mapped to their tags.

        NOTE: Currently unused, likely will be used by some querying tools.
        '''
        for testitem in suite:
            uniq_tags.update(testitem.tags)
            if isinstance(testitem, TestCase):
                itemtags[testitem] = recursive_tags | testitem.tags
            elif isinstance(testitem, TestSuite):
                self._build_tags(testitem, itemtags, testitem.tags
                                 | recursive_tags, uniq_tags)
            else:
                assert False, _util.unexpected_item_msg

    def drop_caches(self):
        self._cached_suitecall = None
        self._cached_tag_index = None

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

                for f in directory:
                    self.load_file(f)

    def load_file(self, path, collection=None):
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
        self.drop_caches()

        if collection is None:
            collection = self._suites

        newdict = {
            '__builtins__':__builtins__,
            '__name__': path_as_modulename(path),
            '__file__': path,
            '__directory__': os.path.dirname(path),
        }

        # TODO: Change the wrapping to a newdict modifcation rather than global
        # wrapping
        self._wrap_init(TestSuite, self._collected_test_items)
        self._wrap_init(TestCase, self._collected_test_items)
        self._wrap_init(Fixture, self._collected_fixtures)

        # Add the file's containing directory to the system path.
        sys.path.insert(0, os.path.dirname(path))
        cwd = os.getcwd()
        os.chdir(os.path.dirname(path))

        def cleanup():
            self._unwrap_init(TestSuite)
            self._unwrap_init(TestCase)
            self._unwrap_init(Fixture)
            self._collected_fixtures = helper.OrderedSet()
            self._collected_test_items = helper.OrderedSet()
            del sys.path[0]
            os.chdir(cwd)

        try:
            execfile(path, newdict, newdict)
        except Exception as e:
            log.warn('Tried to load tests from %s but failed with an'
                    ' exception.' % path)
            log.debug(traceback.format_exc())
            cleanup()
            return

        # Separate the instances so we can manipulate them more easily.
        # We also keep them together so we know ordering.
        test_items = self._collected_test_items
        testcases = helper.OrderedSet()
        testsuites = []

        for item in test_items:
            if isinstance(item, TestCase):
                testcases.add(item)
            elif isinstance(item, TestSuite):
                testsuites.append(item)

        self._index(*self._collected_test_items)
        self._fixtures.extend(self._collected_fixtures)

        if testcases:
            log.display('Discovered %d tests and %d testsuites in %s'
                             '' % (len(testcases), len(testsuites), path))

            # Remove all tests already contained in a TestSuite.
            if testsuites:
                testcases = helper.OrderedSet(testcases)
                for testsuite in testsuites:
                    import pdb; pdb.set_trace()
                    testcases -= helper.OrderedSet(testsuite.testcases)

            # Add any remaining tests to the module TestSuite.
            if len(test_items) >= len(testcases):
                module_testsuite = path_as_testsuite(path)
                testsuites.append(module_testsuite)
                for test_item in test_items:
                    if isinstance(test_item, TestCase):
                        module_testsuite.append(test_item)

            collection.extend(testsuites)

        elif testsuites:
            log.warn('No tests discovered in %s, but found %d '
                            ' TestSuites' % (path, len(testsuites)))
        else:
            log.warn('No tests discovered in %s' % path)

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

    def _index(self, *testitems):
        def add_to_index(item, index, rindex):
            if item in rindex:
                raise DuplicateTestItemError()
            rindex[item] = item.uid
            index[item.uid] = item

        for item in testitems:
            if isinstance(item, TestCase):
                add_to_index(item, self._test_index, self._test_rindex)
            elif isinstance(item, TestSuite):
                add_to_index(item, self._suite_index, self._suite_rindex)
            elif __debug__:
                raise AssertionError('Only can enumerate TestCase and'
                                     ' TestSuite objects')

class DuplicateTestItemError(Exception):
    pass
