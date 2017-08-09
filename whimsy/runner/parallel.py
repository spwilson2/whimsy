import abc
import multiprocessing
from itertools import imap

class WorkerPool(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, threads):
        self.threads = threads
        self.parallel = threads and threads > 1

    @abc.abstractproperty
    def pool(self):
        pass

    def imap_unordered(self, map_function, args):
        print 'imap unordered'
        if self.parallel:
            return self._imap_parallel(map_function, args)
        print 'imap unordered'
        return self._imap_serial(map_function, args)

    _imap_serial = imap

    def _imap_parallel(self, map_function, args):
        return self.pool.imap_unordered(map_function, args)

class MulticoreWorkerPool(WorkerPool):
    '''
    A worker takes jobs of its queue used to initalize it and sends them to
    the process which it wraps to execute.

    :param function: A module level function to supply jobs to. (Note: Must be
        exposed globaly by a module.
    '''
    def __init__(self, threads=None):
        super(MulticoreWorkerPool, self).__init__(threads)

        self._process_pool = None
        if self.parallel:
            self._process_pool = multiprocessing.Pool(threads)

    @property
    def pool(self):
        return getattr(self, '_process_pool', None)

    def _imap_parallel(self, map_function, args):
        jobs = ((map_function, arg) for arg in args)
        try:
            gen = super(MulticoreWorkerPool, self)._imap_parallel(
                    subprocess_exception_wrapper,
                    jobs
            )

            # We need to use polling since termination is broken in python2.
            # (Blocking waits do not internally poll for us.)
            #
            # NOTE: The cpython library will automatically poll faster than
            # the time we give it.
            for res in gen:
                yield res

        except KeyboardInterrupt:
            self._process_pool.terminate()
            self._process_pool.join()
            raise

class SubprocessException(Exception):
    '''
    Exception represents an exception that occured in a child python
    process.
    '''

def subprocess_exception_wrapper(args):
    '''
    Wraps a python child process with a function that will enable tracebacks
    to be printed from child python processes.
    '''
    import traceback
    import sys
    (function, args) = args
    try:
        return function(args)
    except:
        raise SubprocessException("".join(traceback.format_exception(*sys.exc_info())))
