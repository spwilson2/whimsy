import Queue
import multiprocessing
from multiprocessing.managers import SyncManager
import threading

def simple_print(args):
    print args

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

        # Spawn a thread to also participate in work in case we are a server
        # with no workers.
        self.work_client = WorkClient(*self.dest)
        self.work_client.daemon = True
        self.work_client.start()

    def shutdown(self):
        '''
        Note: It's technically better form to be sure to call this function,
        however it often takes a long time for the work_client to close its
        socket connection to the queue_sever.
        '''
        self.queue_server.shutdown()
        self.work_client.join()

    def imap_unordered(self, function, args):
        work_queue = self.queue_server.get_work_queue()
        result_queue = self.queue_server.get_result_queue()
        length = 0
        for arg in args:
            length += 1
            work_queue.put((function, arg))

        for _ in range(length):
            yield result_queue.get()

class WorkClient(threading.Thread):
    # Signals sent through the work queue.
    def __init__(self, hostname, port, passkey):
        self.dest = (hostname, port, passkey)
        self.queue_client = WorkQueueClient(hostname, port, passkey)
        super(WorkClient, self).__init__()

    def run(self):
        self.queue_client.connect()
        work_queue = self.queue_client.get_work_queue()
        result_queue = self.queue_client.get_result_queue()
        self.imap_task(work_queue, result_queue)

    @staticmethod
    def imap_task(wq, rq):
        try:
            while True:
                (function, arg) = wq.get()
                rq.put(function(arg))
        except EOFError:
            return

server_credentials = ('', 11112, 'hi')

#clients = []
#for i in range(0):
#    client = WorkClient(*server_credentials)
#    t = threading.Thread(target=lambda:client.start())
#    t.daemon = True
#    t.start()
#    clients.append(client)
#
#server = WorkServer(*server_credentials)
#server.start()
#
#iterator = server.imap_unordered(simple_print, range(5))
#for val in iterator:
#    val
#
#server.shutdown()
