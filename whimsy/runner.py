import suite

class Runner(object):
    '''
    The default runner class used for running test suites and cases.
    '''
    def run_all(self):
        '''
        Run all tests.

        Note: This isn't likely a realistic use function. In general it's
        expected to request certain tags to be run. This will just run all
        tests collected in the top_level test suite.
        '''
        print(suite.TestSuite.list_all())
