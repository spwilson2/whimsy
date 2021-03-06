import os
import copy

from ..test import TestFunction
from ..suite import TestList, TestSuite
from ..helper import log_call, CalledProcessError
from ..config import constants, config
from ..loader import no_collect
from fixture import TempdirFixture, Gem5Fixture, VariableFixture
import verifier

def gem5_verify_config(name,
                       config,
                       config_args,
                       verifiers,
                       gem5_args=tuple(),
                       tags=[],
                       fixtures=[],
                       valid_isas=constants.supported_isas,
                       valid_optimizations=constants.supported_optimizations):
    '''
    Helper class to generate common gem5 tests using verifiers.

    The generated TestSuite will run gem5 with the provided config and
    config_args. After that it will run any provided verifiers to verify
    details about the gem5 run.

    .. seealso::  For the verifiers see :mod:`whimsy.gem5.verifier`

    :param name: Name of the test.
    :param config: The config to give gem5.
    :param config_args: A list of arguments to pass to the given config.

    :param verifiers: An iterable with Verifier instances which will be placed
        into a suite that will be ran after a gem5 run.

    :param gem5_args: An iterable with arguments to give to gem5. (Arguments
        that would normally go before the config path.)

    :param valid_isas: An interable with the isas that this test can be ran
        for. If None given, will run for all supported_isas.

    :param valid_optimizations: An interable with the optimization levels that
        this test can be ran for. (E.g. opt, debug)
    '''
    for verifier in verifiers:
        no_collect(verifier)

    given_fixtures = []
    given_fixtures.extend(fixtures)
    fixtures = given_fixtures
    original_verifiers = verifiers

    testsuites = []
    for opt in valid_optimizations:
        for isa in valid_isas:

            # Create a tempdir fixture to be shared throughout the test.
            tempdir = TempdirFixture(build_once=True, lazy_init=True)
            gem5_returncode = VariableFixture(
                    name=constants.gem5_returncode_fixture_name)

            # Common name of this generated testcase.
            _name = '{given_name} [{isa} - {opt}]'.format(
                    given_name=name,
                    isa=isa,
                    opt=opt)

            # Create the running of gem5 subtest.
            # NOTE: We specifically create this test before our verifiers so
            # this is listed first.
            gem5_subtest = TestFunction(
                    _create_test_run_gem5(config, config_args, gem5_args),
                    name=_name)

            # Create copies of the verifier subtests for this isa and
            # optimization.
            verifier_tests = []
            for verifier in original_verifiers:
                verifier = copy.copy(verifier)
                verifier._name = '{name} ({vname} verifier)'.format(
                        name=_name,
                        vname=verifier.name)

                verifier_tests.append(verifier)

            # Place the verifier subtests into a collection.
            verifier_collection = TestList(verifier_tests, fail_fast=False)

            # Create the gem5 target for the specific architecture and
            # optimization level.
            fixtures = copy.copy(given_fixtures)
            fixtures.append(Gem5Fixture(isa, opt))
            fixtures.append(tempdir)
            fixtures.append(gem5_returncode)
            # Add the isa and optimization to tags list.
            tags = copy.copy(tags)
            tags.extend((opt, isa))

            # Place our gem5 run and verifiers into a failfast test
            # collection. We failfast because if a gem5 run fails, there's no
            # reason to verify results.
            gem5_test_collection =  TestList(
                    (gem5_subtest, verifier_collection),
                    fail_fast=True)

            # Finally construct the self contained TestSuite out of our
            # tests.
            testsuites.append(TestSuite(
                _name,
                fixtures=fixtures,
                tags=tags,
                tests=gem5_test_collection))
    return testsuites

def _create_test_run_gem5(config, config_args, gem5_args):
    def test_run_gem5(fixtures):
        '''
        Simple \'test\' which runs gem5 and saves the result into a tempdir.

        NOTE: Requires fixtures: tempdir, gem5
        '''

        if gem5_args is None:
            _gem5_args = tuple()
        elif isinstance(gem5_args, str):
            # If just a single str, place it in an iterable
            _gem5_args = (gem5_args,)
        else:
            _gem5_args = gem5_args

        # FIXME/TODO: I don't like the idea of having to modify this test run
        # or always collect results even if not using a verifier. There should
        # be some configuration in here that only gathers certain results for
        # certain verifiers.
        #
        # I.E. Only the returncode verifier will use the gem5_returncode
        # fixture, but we always require it even if that verifier isn't being
        # ran.

        returncode = fixtures[constants.gem5_returncode_fixture_name]
        tempdir = fixtures[constants.tempdir_fixture_name].path
        gem5 = fixtures[constants.gem5_binary_fixture_name].path
        command = [
            gem5,
            '-d',  # Set redirect dir to tempdir.
            tempdir,
            '-re',# TODO: Change to const. Redirect stdout and stderr
        ]
        command.extend(_gem5_args)
        command.append(config)
        # Config_args should set up the program args.
        command.extend(config_args)
        try:
            log_call(command)
        except CalledProcessError as e:
            returncode.value = e.returncode
            if e.returncode != 1:
                raise e
        else:
            returncode.value = 0
    return test_run_gem5
