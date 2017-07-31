import os
import re
import sys
import traceback
from types import MethodType

from fixture import Fixture
from helper import OrderedSet, absdirpath, OrderedDict
from logger import log
from suite import TestSuite, SuiteList, TestList
from test import TestCase

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
    return TestSuite(os.path.split(absdirpath(filepath))[-1],
        *args, **kwargs)

if __debug__:
    def _assert_files_in_same_dir(files):
        if files:
            directory = os.path.dirname(files[0])
            for f in files:
                assert os.path.dirname(f) == directory

class _MethodWrapper(object):
    _sentinal = object()
    def __init__(self, cls, method_name, callback):
        self._callback = callback
        self._cls = cls
        self._method_name = method_name
        self._old_method = self._sentinal
        if __debug__:
            self._replaced_method = None

    def wrap(self):
        old_method = getattr(self._cls, self._method_name, self._sentinal)
        sentinal = self._sentinal
        callback = self._callback

        def combined_method(*args, **kwargs):
            if old_method not in (sentinal, NotImplemented):
                old_method(*args, **kwargs)
            callback(*args, **kwargs)

        replacement = combined_method
        self._old_method = old_method
        setattr(self._cls, self._method_name, replacement)
        self._replaced_method = getattr(self._cls, self._method_name)

    def unwrap(self):
        if self._old_method != self._sentinal:
            assert getattr(self._cls, self._method_name) == self._replaced_method, \
                    "%s's %s has changed, we can not restore it." \
                    % (self._cls, self._method_name)
            setattr(self._cls, self._method_name, self._old_method)
        else:
            delattr(self._cls, self._method_name)


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
        self.tags = tags

        # List of all the fixtures we have collected.
        self._fixtures = []

        # Tests and suites are identified by the test loader in a format that
        # enforces uniqueness - both so users and the test system can identify
        # unique tests.
        # Reverse index: testitem->uid
        self._test_index  = OrderedDict()
        self._suite_index = OrderedDict()

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
        self._collected_test_items = OrderedSet()
        self._collected_fixtures = OrderedSet()


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

    def get_uid(self, uid):
        '''Return the test item with the given uid.'''
        return self._test_index.get(uid, self._suite_index.get(uid, None))

    def tag_index(self, tag):
        '''
        Return a list of test items with the given tag.
        '''
        if self._cached_tag_index is None:
            self._build_tags(self._suites, uniq_tags)

        return self._cached_tag_index.get(tag, [])

    def _build_tags(self, suites, uniq_tags):
        '''
        Build an dictionary index of all TestSuite and TestCases stored in the
        given suite mapped to their tags.

        NOTE: Currently unused, likely will be used by some querying tools.
        '''
        item_tags = {}
        uniq_tags = set()
        for test_suite in suites:
            item_tags[test_suite] = test_suite.tags
            uniq_tags.update(test_suite.tags)
            for test in test_suite:
                item_tags[test] = test.tags
                uniq_tags.update(test.tags)

        # Build Reverse the index of single tag to list of items
        self._cached_tag_index = {}
        for item, itemtags in item_to_tags.iteritems():
            for _tag in uniq_tags:
                if _tag in itemtags:
                    testlist = self._cached_tag_index.setdefault(_tag, [])
                    testlist.append(item)


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

        self._wrap_collection(TestSuite, self._collected_test_items)
        self._wrap_collection(TestCase, self._collected_test_items)
        self._wrap_collection(Fixture, self._collected_fixtures)

        # Add the file's containing directory to the system path.
        sys.path.insert(0, os.path.dirname(path))
        cwd = os.getcwd()
        os.chdir(os.path.dirname(path))

        def cleanup():
            self._unwrap_collection(TestSuite)
            self._unwrap_collection(TestCase)
            self._unwrap_collection(Fixture)
            self._collected_fixtures = OrderedSet()
            self._collected_test_items = OrderedSet()
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
        testcases = OrderedSet()
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
                testcases = OrderedSet(testcases)
                for testsuite in testsuites:
                    testcases -= OrderedSet(testsuite.testcases)

            # Add any remaining tests to the module TestSuite.
            if len(test_items) >= len(testcases):
                module_testsuite = path_as_testsuite(path)
                testsuites.append(module_testsuite)
                for test_item in test_items:
                    if isinstance(test_item, TestCase):
                        module_testsuite.append(test_item)

                # Add our new testsuite into the index as well
                self._index(module_testsuite)


            collection.extend(testsuites)

        elif testsuites:
            log.warn('No tests discovered in %s, but found %d '
                            ' TestSuites' % (path, len(testsuites)))
        else:
            log.warn('No tests discovered in %s' % path)

        cleanup()


    def _wrap_collection(self, cls, collector):
        '''
        Wrap the given cls' __init__ method with a wrapper that will keep an
        OrderedSet of the instances.

        Note: If any other class monkey patches the __init__ method as well,
        this will lead to issues. Keep __debug__ mode enabled to enable checks
        that this never happens.
        '''
        assert cls not in self._wrapped_classes
        def instance_collector(self, *args, **kwargs):
            collector.add(self)
        def instance_decollector(self):
            collector.remove(self)

        # Python2 MethodTypes are different than functions.
        #our_wrapper = MethodType(instance_collect_wrapper, None, cls)
        init_wrapper = _MethodWrapper(cls, '__init__', instance_collector)
        del_wrapper = _MethodWrapper(cls, 'unregister', instance_decollector)
        init_wrapper.wrap()
        del_wrapper.wrap()
        self._wrapped_classes[cls] = (init_wrapper, del_wrapper)

    def _unwrap_collection(self, cls):
        '''
        Note: If any other class monkey patches the __init__ method as well,
        this will lead to issues. Keep __debug__ mode enabled to enable checks
        that this never happens.
        '''
        (init_wrapper, del_wrapper) = self._wrapped_classes[cls]
        init_wrapper.unwrap()
        del_wrapper.unwrap()
        del self._wrapped_classes[cls]

    def _index(self, *testitems):
        def add_to_index(item, index, rindex):
            if item in index:
                raise DuplicateTestItemError(
                        "Item uid: '%s' already exists" % item.uid)
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
