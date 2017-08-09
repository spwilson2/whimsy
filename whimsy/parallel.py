import multiprocessing

from loader import TestLoader
from config import config as global_config
import runner 
from result import InternalLogger

class Job(object):
    '''
    Represents a task for a :class:`whimsy.parallel.Worker`.
    '''
    def __init__(self, uid):
        ''':param uid: Uid of the task to run.'''
        self.uid = uid

class WorkerPool(object):
    '''
    A worker takes jobs of its queue used to initalize it and sends them to
    the process which it wraps to execute.

    :param function: A module level function to supply jobs to. (Note: Must be
        exposed globaly by a module.
    '''
    def __init__(self, threads):
        self.threads = threads
        if threads > 1:
            self._process_pool = multiprocessing.Pool(threads)
        else:
            self._process_pool = None

    def _schedule_parallel(self, jobs, map_function):
        try:
            gen = self._process_pool.imap_unordered(map_function, 
                                                    jobs,
                                                    chunksize=1)

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

    def _schedule_sequential(self, jobs, map_function):
        for job in jobs:
            yield map_function(job)

    def schedule(self, jobs, map_function):
        '''
        Main runloop for the worker.

        Sends Job objects to the underlying child process while there are any
        remaining.
        '''
        if self._process_pool:
            return self._schedule_parallel(jobs, map_function)
        return self._schedule_sequential(jobs, map_function)

if __name__ == '__main__':
    q = Queue.Queue()
    worker = WorkerPool(range(10))
    worker.main()
