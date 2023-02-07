import logging
from collections import deque
from pyhtmlgui import ObservableList


class Logger():
    def __init__(self, level = logging.DEBUG, quiet = False):
        self.logs = ObservableList()
        handlers = [LogHandler(self.logs), ]
        if not quiet:
            handlers.append(logging.StreamHandler())
        logging.basicConfig(
            format   = '[%(asctime)s] %(levelname)s: %(name)s: %(message)s',
            datefmt  = '%Y-%m-%d %H:%M:%S',
            level    = level,
            handlers = handlers)

class LogHandler(logging.Handler):
    def __init__(self, target_log):
        super(LogHandler, self).__init__()
        self.logs = target_log
        self._cnt = len(self.logs)

    def emit(self, record):
        self.format(record)
        self.logs.insert(0, LogRecord(record.asctime, record.levelname, record.name, record.message))
        if self._cnt >= 1000:
            del self.logs[-1]
        else:
            self._cnt += 1

class LogRecord():
    def __init__(self, timestamp, levelname, name, message):
        self.timestamp = timestamp
        self.levelname = levelname
        self.name = name
        self.message = message
