import abc
import multiprocessing
from multiprocessing.managers import SyncManager
import Queue
from itertools import imap

from ..config import config
from ..logger import log

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
            #self._process_pool = multiprocessing.Pool(threads)
            self._process_pool = ComplexMulticorePool(threads)

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

class ComplexMulticorePool(WorkerPool):
    '''
    Class serves as an example of how to make an unordered imap worker pool. It
    serves as a drop in replacement for the multiprocessing.Pool.
    '''
    def __init__(self, threads=None):
        super(ComplexMulticorePool, self).__init__(threads)
        credentials = ('', 11112, 'hi') # TODO/FIXME, use the config.
        self.server = WorkServer(*credentials)

        if self.parallel:
            #self._additional_workers = [WorkClient(*credentials)]
            pass

    @property
    def pool(self):
        return self.server

    def _imap_parallel(self, function, args):
        self.server.start()
        for i in self.server.imap_unordered(function, args):
            yield i
        self.server.shutdown()

class WorkQueueServer(SyncManager):
    def __init__(self, hostname, port, passkey):

        self.work_queue = Queue.Queue()
        self.result_queue = Queue.Queue()

        self.register('get_work_queue', lambda:self.work_queue)
        self.register('get_result_queue', lambda:self.result_queue)

        super(WorkQueueServer, self).__init__((hostname, port), passkey)

class WorkQueueClient(SyncManager):
    def __init__(self, hostname, port, passkey):
        self.register('get_work_queue')
        self.register('get_result_queue')
        super(WorkQueueClient, self).__init__((hostname, port), passkey)

class WorkServer(object):
    def __init__(self, hostname, port, passkey):
        self.queue_server = WorkQueueServer(hostname, port, passkey)
        self.dest = (hostname, port, passkey)

        # Indicates that a imap function is already in progress.
        self.in_progress = False
        self.started = False

    def start(self):
        # Start the work queue manager.
        self.queue_server.start()

        # Spawn a subprocess to also participate in work in case we are a server
        # with no workers. NOTE: We use a subprocess rather than a thread so we
        # are not required to wait for the sockets to cleanup.
        self.work_client = WorkClient(*self.dest)
        self.work_client.daemon = True
        self.work_client.start()

    def shutdown(self):
        self.queue_server.shutdown()
        # Note: It will take a decent amount of time for the work_client to close
        # its sockets so we don't bother joining. Just let the process cleanup
        # on its own.
        # self.p.terminate()
        # self.work_client.join()

    def imap_unordered(self, function, args):
        work_queue = self.queue_server.get_work_queue()
        result_queue = self.queue_server.get_result_queue()
        length = 0
        for arg in args:
            length += 1
            work_queue.put((function, arg))

        for _ in range(length):
            yield result_queue.get()

class WorkClient(multiprocessing.Process):
    # Signals sent through the work queue.
    def __init__(self, hostname, port, passkey):
        self.dest = (hostname, port, passkey)
        self.queue_client = WorkQueueClient(hostname, port, passkey)
        super(WorkClient, self).__init__()

    def run(self):
        self.queue_client.connect()
        log_if_client(log.bold, 'Connected to test server.')
        work_queue = self.queue_client.get_work_queue()
        result_queue = self.queue_client.get_result_queue()
        self.imap_task(work_queue, result_queue)
        log_if_client(log.bold, 'Work completed for test server, closing.')

    @staticmethod
    def imap_task(wq, rq):
        try:
            while True:
                (function, arg) = wq.get()
                rq.put(function(arg))
        except EOFError:
            return

def runloop(*credentials):
    work_client = WorkClient(*credentials)
    work_client.daemon = True
    work_client.start()
    work_client.join()

def log_if_client(callback, *args, **kwargs):
    if config.command == 'client':
        callback(*args, **kwargs)


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
