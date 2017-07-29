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
        with open(config.result_path, 'w') as result_file:
            testrunner = runner.Runner(loader.suites,
                    (result.InternalLogger(result_file),))

            logger.log.display(terminal.separator())
            logger.log.bold('Running Tests')
            logger.log.display('')
            if config.uid:
                results = testrunner.run_uid(config.uid)
            else:
                results = testrunner.run()

        #if results is not None:
        #    logger.log.display(terminal.separator())
        #    logger.log.bold('Summarizing Test Results')
        #    logger.log.display('')

        #    # Save the results in a format which we can retrieve later.
        #    formatter = result.InternalFormatter(results)

        #    with open(config.result_path, 'w') as result_file:
        #        formatter.dump(result_file)

        #    formatter = result.ConsoleFormatter(results)
        #    # This will always contain a summary separator.
        #    logger.log.display(str(formatter))
        #else:
        #    logger.log.display(terminal.separator())

def dorerun():
    # Load previous results
    # TODO Catch bad file path error or load error.
    old_formatter = result.InternalFormatter(config.result_path, fromfile=True)

    # Load tests
    loader = load_tests()
    testrunner = runner.Runner(loader.suite)

    results = result.TestResultContainer()
    # Get the self contained suites which hold tests that fail and run each.
    for suite in old_formatter.result.iter_self_contained():
        if suite.outcome == result.Result.FAIL:
            #TODO: Likely will need to improve performance since this will
            # require re-enumerating fixtures for this uid each time.
            results.add_results(testrunner.run_uid(suite.uid))

    if results is not None:
        logger.log.display(terminal.separator())
        logger.log.bold('Summarizing Test Results')
        logger.log.display('')

        # Save the results in a format which we can retrieve later.
        formatter = result.InternalFormatter(results)

        with open(config.result_path, 'w') as result_file:
            formatter.dump(result_file)

        formatter = result.ConsoleFormatter(results)
        # This will always contain a summary separator.
        logger.log.display(str(formatter))
    else:
        logger.log.display(terminal.separator())


def dolist():
    loader = load_tests()
    if config.tags:
        query.list_tests_with_tags(loader, config.tags)
    elif config.suites:
        query.list_suites(loader)
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
