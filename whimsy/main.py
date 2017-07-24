#!/usr/bin/env python2
'''
The main source for whimsy. Ties together the default test runners and
loaders.

Discovers and runs all tests from a given root directory.
'''
import whimsy.logger as logger
import whimsy.loader as loader
import whimsy.runner as runner
import whimsy.result as result
import whimsy.terminal as terminal
import whimsy.query as query
from whimsy.config import config

def load_tests():
    '''
    Create a TestLoader and load tests for the directory given by the config.
    '''
    testloader = loader.TestLoader()
    logger.log.info(terminal.separator())
    logger.log.info('Loading Tests')
    testloader.load_root(config.directory)
    logger.log.info(terminal.separator())
    return testloader

def dorun():
        loader = load_tests()
        testrunner = runner.Runner(loader.suite)

        results = testrunner.run()

        formatter = result.ConsoleFormatter(results)
        print(formatter)

def dolist():
    loader = load_tests()
    query.list_fixtures(loader)
    query.list_tests(loader)
    query.list_suites(loader)
    query.list_tags(loader)

def main():
    # Start logging verbosity at its minimum
    logger.set_logging_verbosity(0)
    # Then do parsing of the arguments to init config.
    logger.set_logging_verbosity(config.verbose)

    if config.run:
        dorun()
    if config.list:
        dolist()
