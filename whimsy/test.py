import abc
import copy
from unittest import FunctionTestCase as _Ftc
from functools import partial

from config import config, constants
import helper
import fixture
import suite
import os
import _util
from suite import TestList

def _as_kwargs(**kwargs):
    return kwargs

def steal_unittest_assertions(module):
    '''
    Attach all the unittest.TestCase assertion helpers to the given modules
    namespace.
    '''
    # Since unittest assertion helpers all need an instance to work, we
    # need to do some partial application with a wrapper function.
    fake_testcase = _Ftc(None)
    for item in dir(_Ftc):
        if item.startswith('assert'):
            module[item] = partial(getattr(_Ftc, item), fake_testcase)

# Export the unittest assertion helpers from this module.
steal_unittest_assertions(globals())

class TestingException(Exception):
    '''Common ancestor for manual Testing Exceptions.'''
class TestFailException(TestingException):
    '''Signals that a test has failed.'''
class TestSkipException(TestingException):
    '''Signals that a test has been skipped.'''

def fail(message):
    '''Cause the current test to fail with the given message.'''
    raise TestFailException(message)

def skip(message):
    '''Cause the current test to skip with the given message.'''
    raise TestSkipException(message)

class TestCase(object):
    '''
    For example: in a test were we run gem5 and verify output. The combination
    of running gem5 and verifying output forms a TestCase. Whereas it would be
    imposible to run verify output if gem5 was not run first. In this example
    both gem5 and verify output would be subtests of a single TestCase.
    '''
    __metaclass__ = abc.ABCMeta
    def __init__(self, name, tags=None, fixtures=None):
        '''
        __init__ must be called in subclasses for self contained tests to be
        recognized by the test loader.
        '''
        if fixtures is None:
            fixtures = {}
        elif not isinstance(fixtures, dict):
            fixtures = {fixture.name: fixture for fixture in fixtures}
        self.fixtures = fixtures

        if tags is None:
            tags = set()
        self.tags = set(tags)

        self._name = name
        self._path = os.getcwd()

    @property
    def uid(self):
        return _util.uid(self)
    @property
    def path(self):
        return self._path
    @property
    def name(self):
        return self._name
    @abc.abstractmethod
    def __call__(self, fixtures):
        pass
    # This is a method that will be created by the test loader in order to
    # manually remove a test.
    unregister = NotImplemented

class TestFunction(TestCase):
    __metaclass__ = abc.ABCMeta
    def __init__(self, test, name=None, *args, **kwargs):
        if name is None:
            # If not given a name, take the name of the function.
            name = test.__name__
        super(TestFunction, self).__init__(name, *args, **kwargs)
        self._test_function = test

    def __call__(self, fixtures):
        '''
        Override TestCase definition of __call__
        '''
        self._test_function(fixtures)


def gem5_verify_config(name,
                       config,
                       config_args,
                       verifiers,
                       tags=[],
                       fixtures=[],
                       valid_isas=None,
                       valid_optimizations=('opt',)):
    '''
    Runs the given program using the given config and passes if no exception
    was thrown.

    NOTE: This is not an actual testcase, it generates a group of tests which
    can be used by gem5_test.

    :param name: Name of the test.
    :param config: The config to give gem5.
    :param program: The executable to run using the config.

    :param verifiers: An iterable with Verifier instances which will be placed
    into a suite that will be ran after a gem5 run.

    :param valid_isas: An interable with the isas that this test can be ran
    for.

    :param valid_optimizations: An interable with the optimization levels that
    this test can be ran for. (E.g. opt, debug)
    '''
    if valid_isas is None:
        valid_isas = constants.supported_isas

    for verifier in verifiers:
        verifier.unregister()

    for opt in valid_optimizations:
        for isa in valid_isas:

            # Create a tempdir fixture to be shared throughout the test.
            tempdir = fixture.TempdirFixture(cached=True, lazy_init=True)

            # Common name of this generated testcase.
            _name = '{given_name} [{isa} - {opt}]'.format(
                    given_name=name,
                    isa=isa,
                    opt=opt)

            # Create copies of the verifier subtests for this isa and
            # optimization.
            verifier_tests = []
            for verifier in verifiers:
                verifier = copy.copy(verifier)
                verifier._name = '{name} ({vname} verifier)'.format(
                        name=_name,
                        vname=verifier.name)

                verifier_tests.append(verifier)

            # Place the verifier subtests into a collection.
            verifier_collection = TestList(verifier_tests, fail_fast=False)

            # Create the gem5 target for the specific architecture and
            # optimization level.
            fixtures = copy.copy(fixtures)
            fixtures.append(fixture.Gem5Fixture(isa, opt))
            fixtures.append(tempdir)
            # Add the isa and optimization to tags list.
            tags = copy.copy(tags)
            tags.extend((opt, isa))

            # Create the running of gem5 subtest.
            gem5_subtest = TestFunction(
                    _create_test_run_gem5(config, config_args),
                    name=_name)

            # Place our gem5 run and verifiers into a failfast test
            # collection. We failfast because if a gem5 run fails, there's no
            # reason to verify results.
            gem5_test_collection =  TestList(
                    (gem5_subtest, verifier_collection),
                    fail_fast=True)

            # Finally construct the self contained TestSuite out of our
            # tests.
            a = suite.TestSuite(
                    _name,
                    fixtures=fixtures,
                    tags=tags,
                    tests=gem5_test_collection)

def _create_test_run_gem5(config, config_args):
    def test_run_gem5(fixtures):
        '''
        Simple \'test\' which runs gem5 and saves the result into a tempdir.

        NOTE: Requires fixtures: tempdir, gem5
        '''
        tempdir = fixtures['tempdir'].path
        gem5 = fixtures['gem5'].path
        command = [
            gem5,
            '-d',  # Set redirect dir to tempdir.
            tempdir,
            '-re',# TODO: Change to const. Redirect stdout and stderr
            config
        ]
        # Config_args should set up the program args.
        command.extend(config_args)
        try:
            helper.log_call(command)
        except helper.CalledProcessError as e:
            if e.returncode != 1:
                raise e
    return test_run_gem5


def testfunction(function=None, name=None, tag=None, tags=None, fixtures=None):
    # If tag was given, then the test will be marked with that single tag.
    # elif tags was given, then the test will be marked with all those tags.
    if tag is not None:
        tags = set((tag,))
    elif tags is not None:
        tags = set(tags)

    def testfunctiondecorator(function):
        '''Decorator used to mark a function as a test case.'''
        TestFunction(function, name=name, tags=tags, fixtures=fixtures)
        return function
    if function is not None:
        return testfunctiondecorator(function)
    else:
        return testfunctiondecorator

if __name__ == '__main__':
    print('Self-test')
    print('Test that we can create a dereived tests from TestCase.')
    class NewBase(TestCase):
        def test(self, fixtures):
            pass

    print('Test that a test must have the test method defined.')
    try:
        class NewBase(TestCase):
            pass
    except:
        pass
    else:
        assert False, 'Did not raise an exception for an undefined test method.'
