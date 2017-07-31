import logging as _logging
import sys
import functools

import terminal as termcap

# Logging level to be used to always display information to the user
def add_logging_level(name, val):
    name = name.lower()
    _logging.addLevelName(val, name.upper())

    def log_at_level(self, message, *args, **kwargs):
        if self.isEnabledFor(val):
            self._log(val, message, args, **kwargs)
    # Add the logging helper function as lowercase
    setattr(
        _logging.Logger,
        name.lower(),
        log_at_level
    )

    # Add the value to the naming module as CAPITALIZED
    globals()[name.upper()] = val

# Add all default logging levels to this module
for level in ('ERROR', 'DEBUG', 'FATAL', 'INFO', 'WARN'):
    globals()[level] = getattr(_logging, level)

# The minimum level which will always be displayed no matter verbosity.
always_display_level = WARN

# Logging level used to display bold information for users.
add_logging_level('bold', 1000)
# Logging level to always output (Use for UI stuff.)
add_logging_level('display', 999)
# Logging level used to log captured print statements
# (any output to sys.stdout)
add_logging_level('print', 998)

assert DISPLAY > always_display_level
assert BOLD > always_display_level

# Logging level will be incredibly verbose, used to trace through testing.
add_logging_level('trace', 1)

def set_logging_verbosity(verbosity):
    log.setLevel(max(always_display_level - verbosity * 10, TRACE))

#
class StreamToLogger(object):
    '''
    Fake file-like stream object that redirects writes to a logger instance.

    Use to capture stdout and stderr from python.

    https://www.electricmonk.nl/log/2011/08/14/\
redirect-stdout-and-stderr-to-a-logger-in-python/
    '''
    def __init__(self, logger, log_level=INFO):
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
        BOLD: color.White + color.Bold,
        FATAL: color.Red,
        WARN: color.Yellow
    }

    def __init__(self):
        pass

    def format(self, record):
        color_str = self.level_colormap.get(record.levelno, self.color.Normal)
        return color_str + record.msg + self.reset

# The root logger for whimsy
log = _logging.getLogger('Whimsy Console Logger')

# Redirect log back to stdout so if we redirect the log we
# still see it in the console.
saved_stderr = sys.stderr
saved_stdout = sys.stdout

stdout_logger = _logging.StreamHandler(saved_stdout)
stdout_logger.formatter = ConsoleLogFormatter()
log.addHandler(stdout_logger)
