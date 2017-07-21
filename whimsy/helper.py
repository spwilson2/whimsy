'''
Helper classes for writing tests with this test library.
'''
import logging
import subprocess
import tempfile
import threading

import whimsy.logger as logger

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

if __name__ == '__main__':
    p = Popen(['echo', 'hello'])
    p.poll()
    print(p.communicate())
    log_call(' '.join(['echo', 'hello', ';sleep 3', '; echo yo']), shell=True)
