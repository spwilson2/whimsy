import logging
import sys

import terminal as termcap

# Logging level to be used to always display information to the user
INFORM = 1000
logging.addLevelName(INFORM, "INFORM")
def inform(self, message, *args, **kwargs):
    # For now we can just use print to do this.
    self._log(INFORM, message, args, **kwargs)
logging.Logger.inform = inform
logging.INFORM = INFORM

# https://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/
class StreamToLogger(object):
    '''
    Fake file-like stream object that redirects writes to a logger instance.

    Use to capture stdout and stderr from python.
    '''
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()

class ConsoleLogFormatter(object):
    '''
    Formats output to be sent to an interactive terminal.
    '''

    # For now, just change color based on the logging level.
    color = termcap.get_termcap()
    reset = color.Normal
    level_colormap = {
        logging.INFORM: color.White + color.Bold,
        logging.FATAL: color.Red,
        logging.WARN: color.Yellow,
        logging.INFO: color.Normal,
        logging.DEBUG: color.Cyan,
    }

    def __init__(self):
        pass

    def format(self, record):
        #import pdb; pdb.set_trace()
        color_str = self.level_colormap[record.levelno]
        return color_str + record.msg + self.reset

def set_logging_verbosity(verbosity):
    log.setLevel(max(logging.CRITICAL - verbosity * 10, logging.DEBUG))


# The root logger for whimsy
log = logging.getLogger('Whimsy Console Logger')

# Redirect log back to stdout so if we redirect the log we
# still see it in the console.
saved_stderr = sys.stderr
stdout_logger = logging.StreamHandler(sys.stdout)

# NOTE: This won't capture subprocesses output, the process of doing so would
# invlove using os.dup2 and would mean that we would likely want to run
# imported tests with a modified namespace (for pdb).
stdout_logger.formatter = ConsoleLogFormatter()
log.addHandler(stdout_logger)
sys.stderr = StreamToLogger(log, logging.FATAL)
