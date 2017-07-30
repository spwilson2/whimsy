#!/usr/bin/env python2
'''
The main source for whimsy. Ties together the default test runners and
loaders.

Discovers and runs all tests from a given root directory.
'''
import logger
import loader
import runner
import result
import terminal
import query
from config import config
from tee import tee
from helper import joinpath

# TODO: Standardize separator usage.
# Probably make it the caller responsiblity to place separators and internal
# ones can be used to separate internal input.

def load_tests():
    '''
    Create a TestLoader and load tests for the directory given by the config.
    '''
    testloader = loader.TestLoader()
    logger.log.display(terminal.separator())
    logger.log.bold('Loading Tests')
    logger.log.display('')
    testloader.load_root(config.directory)
    return testloader

def dorun():
        loader = load_tests()
        with open(joinpath(config.result_path, 'pickle'), 'w') as result_file,\
                open(joinpath(config.result_path, 'junit.xml'), 'w') as junit_f:
            testrunner = runner.Runner(
                    loader.suites,
                    (result.JUnitLogger(junit_f, result_file),
                        result.ConsoleLogger()))

            #testrunner = runner.Runner(loader.suites)
            logger.log.display(terminal.separator())
            logger.log.bold('Running Tests')
            logger.log.display('')
            if config.uid:
                results = testrunner.run_uid(config.uid)
            else:
                results = testrunner.run()

def dorerun():
    # Load previous results
    # TODO Catch bad file path error or load error.
    with open(joinpath(config.result_path, 'pickle'), 'r') as old_fstream:
        old_formatter = result.InternalLogger.load(old_fstream)

    # Load tests
    loader = load_tests()

    # Get the self contained suites which hold tests that fail and run each.
    reruns = []
    for suite in old_formatter.suites:
        if suite.outcome in (result.Outcome.FAIL, result.Outcome.ERROR):
            suite = loader.get_uid(suite.uid)
            reruns.append(suite)

    # Run only the suites we need to rerun.
    testrunner = runner.Runner(reruns)
    testrunner.run()

def dolist():
    loader = load_tests()
    if config.tags:
        query.list_tests_with_tags(loader, config.tags)
    if config.suites:
        query.list_suites(loader)
    if config.tests:
        query.list_tests(loader)

def main():
    # Start logging verbosity at its minimum
    logger.set_logging_verbosity(0)
    # Then do parsing of the arguments to init config.
    logger.set_logging_verbosity(config.verbose)

    # 'do' the given command.
    globals()['do'+config.command]()

if __name__ == '__main__':
    main()
