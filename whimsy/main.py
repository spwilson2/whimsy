#!/usr/bin/env python2
'''
The main source for whimsy. Ties together the default test runners and
loaders.

Discovers and runs all tests from a given root directory.
'''
import logger
import query
import result

from helper import joinpath, mkdir_p
from config import config
from loader import TestLoader
from logger import log
from runner import Runner
from terminal import separator

# TODO: Standardize separator usage.
# Probably make it the caller responsiblity to place separators and internal
# ones can be used to separate internal input.

def load_tests():
    '''
    Create a TestLoader and load tests for the directory given by the config.
    '''
    testloader = TestLoader()
    log.display(separator())
    log.bold('Loading Tests')
    log.display('')
    testloader.load_root(config.directory)
    return testloader

def dorun():
        loader = load_tests()

        if config.tags:
            suites = []
            for tag in config.tags:
                suites.extend(loader.suites_with_tag(tag))
        else:
            suites = loader.suites

        # Create directory to save junit and internal results in.
        mkdir_p(config.result_path)

        with open(joinpath(config.result_path, 'pickle'), 'w') as result_file,\
             open(joinpath(config.result_path, 'junit.xml'), 'w') as junit_f:

            junit_logger = result.JUnitLogger(junit_f, result_file)
            console_logger = result.ConsoleLogger()
            loggers = (junit_logger, console_logger)

            log.display(separator())
            log.bold('Running Tests')
            log.display('')
            if config.uid:
                test_item = loader.get_uid(config.uid)
                results = Runner.run_items(test_item)
            else:
                testrunner = Runner(suites, loggers)
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
    testrunner = Runner(reruns)
    testrunner.run()

def dolist():
    loader = load_tests()
    if config.tags:
        query.list_tests_with_tags(loader, config.tags)
    if config.suites:
        query.list_suites(loader)
    if config.tests:
        query.list_tests(loader)
    if config.fixtures:
        query.list_fixtures(loader)
    if config.all_tags:
        query.list_tags(loader)

def main():
    # Start logging verbosity at its minimum
    logger.set_logging_verbosity(0)
    # Then do parsing of the arguments to init config.
    logger.set_logging_verbosity(config.verbose)

    # 'do' the given command.
    globals()['do'+config.command]()

if __name__ == '__main__':
    main()
