import os
import copy

from .. import fixture
from ..test import TestFunction
from ..suite import TestList, TestSuite
from ..helper import log_call
from ..config import constants, config
import verifier

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
            a = TestSuite(
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
            log_call(command)
        except helper.CalledProcessError as e:
            if e.returncode != 1:
                raise e
    return test_run_gem5
