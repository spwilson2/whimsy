class Runner(object):
    '''
    The default runner class used for running test suites and cases.
    '''
    def run_all(self, test_suite):
        '''Run all tests. From the given test_suite.'''
        print(test_suite.items)

    def run_test(self, test):
        '''
        Run the given test.

        This performs the bulkwork of the testing framework.
        1. Handle setup for all fixtures required for the test.
        2. Run the test.
        3. Teardown the fixtures for the test which are tied locally to the
           test?
        '''
