import logging

import whimsy.terminal as termcap

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
        logging.FATAL: color.Red,
        logging.WARN: color.Yellow,
        logging.INFO: color.Cyan,
        logging.DEBUG: color.Normal,
    }

    def __init__(self):
        pass

    def format(self, record):
        color_str = self.level_colormap[record.levelno]
        return color_str + record.msg + self.reset
