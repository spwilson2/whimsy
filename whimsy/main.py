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


def main():
    # Start logging verbosity at its minimum
    logger.set_logging_verbosity(0)
    from whimsy.args import args

    logger.set_logging_verbosity(args.verbose)

    testloader = loader.TestLoader()
    files = testloader.discover_files(args.directory)
    for f in files:
        testloader.load_file(f)

    testrunner = runner.Runner()
    results = testrunner.run_suite(testloader.top_level_suite)

    formatter = result.ConsoleFormatter(results)
    print(formatter)
