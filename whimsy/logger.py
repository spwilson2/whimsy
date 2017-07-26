import logging
import sys
import functools

import terminal as termcap

# Logging level to be used to always display information to the user
def add_logging_level(name, val):
    name = name.lower()
    logging.addLevelName(val, name.upper())

    def log_at_level(self, message, *args, **kwargs):
        if self.isEnabledFor(val):
            self._log(val, message, args, **kwargs)
    # Add the logging helper function as lowercase
    setattr(
        logging.Logger,
        name.lower(),
        log_at_level
    )

    # Add the value to the naming module as CAPITALIZED
    setattr(logging, name.upper(), val)

# The minimum level which will always be displayed no matter verbosity.
always_display_level = logging.WARN

# Logging level used to display bold information for users.
add_logging_level('bold', 1000)
# Logging level to always output (Use for UI stuff.)
add_logging_level('display', 999)
# Logging level used to log captured print statements
# (any output to sys.stdout)
add_logging_level('print', 998)

assert logging.DISPLAY > always_display_level
assert logging.BOLD > always_display_level

# Logging level will be incredibly verbose, used to trace through testing.
add_logging_level('trace', 1)

def set_logging_verbosity(verbosity):
    log.setLevel(max(always_display_level - verbosity * 10, logging.TRACE))

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
        logging.BOLD: color.White + color.Bold,
        logging.FATAL: color.Red,
        logging.WARN: color.Yellow
    }

    def __init__(self):
        pass

    def format(self, record):
        color_str = self.level_colormap.get(record.levelno, self.color.Normal)
        return color_str + record.msg + self.reset

# The root logger for whimsy
log = logging.getLogger('Whimsy Console Logger')

# Redirect log back to stdout so if we redirect the log we
# still see it in the console.
saved_stderr = sys.stderr
saved_stdout = sys.stdout

stdout_logger = logging.StreamHandler(saved_stdout)
stdout_logger.formatter = ConsoleLogFormatter()
log.addHandler(stdout_logger)

# NOTE: This won't capture subprocesses output, the process of doing so would
# invlove using os.dup2 and would mean that we would likely want to run
# imported tests with a modified namespace (for pdb).
sys.stderr = StreamToLogger(log, logging.FATAL)
sys.stdout = StreamToLogger(log, logging.PRINT)
