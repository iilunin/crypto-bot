import logging

LOG_FORMAT = '%(asctime)s[%(levelname)s][%(name)s|%(threadName)s]: %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class Logger:
    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger(self._get_logger_name())

    def logInfo(self, msg):
        self.logger.log(logging.INFO, msg)

    def logWarning(self, msg):
        self.logger.log(logging.WARNING, msg)

    def logError(self, msg):
        self.logger.log(logging.ERROR, msg)

    def _get_logger_name(self):
        return self.__class__.__name__

