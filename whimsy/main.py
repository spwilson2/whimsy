'''
The main source for whimsy. Ties together the default test runners and
loaders.

Discovers and runs all tests from a given root directory.
'''

import argparse

import whimsy.loader as loader
import whimsy.runner as runner

parser = argparse.ArgumentParser()
parser.add_argument('directory')
args = parser.parse_args()

testloader = loader.TestLoader()
files = testloader.discover_files(args.directory)
for f in files:
    testloader.load_file(f)

testrunner = runner.Runner()
testrunner.run_all()
