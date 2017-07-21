'''
The main source for whimsy. Ties together the default test runners and
loaders.

Discovers and runs all tests from a given root directory.
'''

import argparse
import logging
import sys

import whimsy.loader as loader
import whimsy.logger as logger
import whimsy.runner as runner
import whimsy.result as result

parser = argparse.ArgumentParser()
parser.add_argument('directory',
                    help='Directory to start searching for tests in')
parser.add_argument('--verbose', '-v',
                    action='count',
                    default=0,
                    help='Increase verbosity')
args = parser.parse_args()
logger.set_logging_verbosity(args.verbose)

testloader = loader.TestLoader()
files = testloader.discover_files(args.directory)
for f in files:
    testloader.load_file(f)

testrunner = runner.Runner()
results = testrunner.run_suite(testloader.top_level_suite)

formatter = result.ConsoleFormatter(results)
print(formatter)
