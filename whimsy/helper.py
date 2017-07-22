'''
Helper classes for writing tests with this test library.
'''
import logging
import subprocess
import tempfile
import threading

import logger

class Popen(subprocess.Popen):
    '''
    A modified version of Popen where output is automatically piped to
    a tempfile if no pipe was given for the process. If output is expected to
    be large, the user can
    '''

    def __init__(self, args, bufsize=0, executable=None,
             stdin=None, stdout=None, stderr=None, *remainargs, **kwargs):

        self.stdout_f = None
        self.stderr_f = None

        if stdout is None:
            self.stdout_f = tempfile.TemporaryFile()
            stdout = self.stdout_f
            print('Here')
        if stderr is None:
            self.stderr_f = tempfile.TemporaryFile()
            stderr = self.stderr_f
            print('Here')

        super(Popen, self).__init__(args, bufsize=bufsize,
                                    executable=executable, stdin=stdin,
                                    stdout=stdout, stderr=stderr,
                                    *remainargs, **kwargs)
    @staticmethod
    def _read_file(f):
        f.seek(0)
        output = f.read()
        f.truncate()
        return output

    def communicate(self, *args, **kwargs):
        (stdout, stderr) = super(Popen, self).communicate(*args, **kwargs)
        if self.stderr_f is not None:
            stdout = self._read_file(self.stderr_f)
        if self.stdout_f is not None:
            stdout = self._read_file(self.stdout_f)
        return (stdout, stderr)

    def __del__(self):
        '''Destructor automatically closes temporary files if we opened any.'''
        if self.stdout_f is not None:
            self.stdout_f.close()
        if self.stderr_f is not None:
            self.stderr_f.close()

def log_call(*popenargs, **kwargs):
    '''
    Calls the given process and automatically logs the command and output.

    This should be used for fixture setup if the output doesn't need to
    actually be checked.
    '''
    for key in ['stdout', 'stderr']:
        if key in kwargs:
            raise ValueError('%s argument not allowed, it will be'
                             ' overridden.' % key)
    p = Popen(stdout=subprocess.PIPE, stderr=subprocess.PIPE, *popenargs, **kwargs)
    def log_output(log_level, pipe):
        # Read iteractively, don't allow input to fill the pipe.
        for line in iter(pipe.readline, ''):
            line = line.rstrip()
            logger.log.log(log_level, line)

    stdout_thread = threading.Thread(target=log_output,
                                    args=(logging.DEBUG, p.stdout))
    stdout_thread.setDaemon(True)
    stdout_thread.start()

    stderr_thread = threading.Thread(target=log_output,
                                    args=(logging.DEBUG, p.stderr))
    stderr_thread.setDaemon(True)
    stderr_thread.start()

    stdout_thread.join()
    stderr_thread.join()
    return p.returncode


# cacheresult stuff, (From python 3.2+)
class _HashedSeq(list):
    """ This class guarantees that hash() will be called no more than once
        per element.  This is important because the lru_cache() will hash
        the key multiple times on a cache miss.
    """

    __slots__ = 'hashvalue'

    def __init__(self, tup, hash=hash):
        self[:] = tup
        self.hashvalue = hash(tup)

    def __hash__(self):
        return self.hashvalue

def _make_key(args, kwds, typed,
             kwd_mark = (object(),),
             fasttypes = {int, str, frozenset, type(None)},
             tuple=tuple, type=type, len=len):
    """Make a cache key from optionally typed positional and keyword arguments
    The key is constructed in a way that is flat as possible rather than
    as a nested structure that would take more memory.
    If there is only a single argument and its data type is known to cache
    its hash value, then that argument is returned without a wrapper.  This
    saves space and improves lookup speed.
    """
    key = args
    if kwds:
        key += kwd_mark
        for item in kwds.items():
            key += item
    if typed:
        key += tuple(type(v) for v in args)
        if kwds:
            key += tuple(type(v) for v in kwds.values())
    elif len(key) == 1 and type(key[0]) in fasttypes:
        return key[0]
    return _HashedSeq(key)


def cacheresult(function, typed=False):
    '''
    If *typed* is True, arguments of different types will be cached separately.
    For example, f(3.0) and f(3) will be treated as distinct calls with
    distinct results.
    '''
    sentinel = object()          # unique object used to signal cache misses
    make_key = _make_key         # build a key from the function arguments
    cache = {}
    def wrapper(*args, **kwds):
        # Simple caching without ordering or size limit
        key = _make_key(args, kwds, typed)
        result = cache.get(key, sentinel)
        if result is not sentinel:
            return result
        result = function(*args, **kwds)
        cache[key] = result
        return result
    return wrapper

if __name__ == '__main__':
    p = Popen(['echo', 'hello'])
    p.poll()
    print(p.communicate())
    log_call(' '.join(['echo', 'hello', ';sleep 3', '; echo yo']), shell=True)
