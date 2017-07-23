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


def main():
    # Start logging verbosity at its minimum
    logger.set_logging_verbosity(0)
    from whimsy.config import config

    logger.set_logging_verbosity(config.verbose)

    testloader = loader.TestLoader()
    logger.log.info(terminal.separator())
    logger.log.info('Loading Tests')
    testloader.load_root(config.directory)
    logger.log.info(terminal.separator())

    testrunner = runner.Runner(testloader.suite)

    logger.log.info(terminal.separator())
    logger.log.info('Running Tests')
    results = testrunner.run()
    logger.log.info(terminal.separator())

    formatter = result.ConsoleFormatter(results)
    print(formatter)
