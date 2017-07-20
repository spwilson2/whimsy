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

parser = argparse.ArgumentParser()
parser.add_argument('directory',
                    help='Directory to start searching for tests in')
parser.add_argument('--verbose', '-v',
                    action='count',
                    default=0,
                    help='Increase verbosity')
args = parser.parse_args()

def logging_verbosity(verbosity):
    return max(logging.CRITICAL - verbosity * 10, logging.DEBUG)

log = logging.getLogger(__name__)
log.setLevel(logging_verbosity(args.verbose))

saved_stdout = sys.stdout
saved_stderr = sys.stderr
# Redirect log back to stdout so when we redirect it to the log we
# still see it in the console.
stdout_logger = logging.StreamHandler(saved_stdout)
stdout_logger.formatter = logger.ConsoleLogFormatter()
log.addHandler(stdout_logger)
log.warn('Hello')

# Redirect stdout and stderr to logger for the test.
sys.stdout = logger.StreamToLogger(log, logging.INFO)
sys.stderr = logger.StreamToLogger(log, logging.WARN)

testloader = loader.TestLoader()
files = testloader.discover_files(args.directory)
for f in files:
    testloader.load_file(f)

testrunner = runner.Runner()
results = testrunner.run_suite(testloader.top_level_suite)
for result in results:
    print(result.result)

# Restore stdout and stderr
sys.stdout = saved_stdout
sys.stderr = saved_stderr
