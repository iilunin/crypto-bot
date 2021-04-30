import logging
import os
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from os import environ, path, listdir
from os.path import isfile, join

LOG_FORMAT = '%(asctime)s[%(levelname)s][%(name)s|%(threadName)s]: %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

LOG_DIR = environ.get('LOGS_DIR')
CURRENT_LOG_FN = path.join(LOG_DIR, 'log.txt') if LOG_DIR else None

if LOG_DIR:
    handler = RotatingFileHandler(CURRENT_LOG_FN, maxBytes=1048576, backupCount=7)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

class Logger:
    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger(self._get_logger_name())

        if LOG_DIR:
            self.logger.addHandler(handler)

    def logInfo(self, msg):
        self.logger.log(logging.INFO, msg)

    def logWarning(self, msg):
        self.logger.log(logging.WARNING, msg)

    def logError(self, msg):
        self.logger.log(logging.ERROR, msg)

    def logDebug(self, msg):
        self.logger.log(logging.DEBUG, msg)

    def list_files(self):
        if not LOG_DIR:
            return None

        return [f for f in listdir(LOG_DIR) if isfile(join(LOG_DIR, f))]

    def get_file_contents(self, file):
        if not file:
            file = CURRENT_LOG_FN
        f = open(file, 'r')
        return f.read()


    def _get_logger_name(self):
        return self.__class__.__name__

