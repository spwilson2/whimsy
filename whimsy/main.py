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
    from whimsy.args import args

    logger.set_logging_verbosity(args.verbose)

    testloader = loader.TestLoader()
    files = testloader.discover_files(args.directory)

    logger.log.info(terminal.separator())
    logger.log.info('Loading Tests')
    for f in files:
        testloader.load_file(f)
    logger.log.info(terminal.separator())

    logger.log.info(terminal.separator())
    logger.log.info('Running Tests')
    testrunner = runner.Runner()
    results = testrunner.run_suite(testloader.top_level_suite)
    logger.log.info(terminal.separator())

    formatter = result.ConsoleFormatter(results)
    print(formatter)
