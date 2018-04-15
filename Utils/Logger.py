import logging

LOG_FORMAT = '%(asctime)s[%(levelname)s][%(name)s|%(threadName)s]: %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class Logger:
    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger(__class__.__name__)

    def logInfo(self, msg):
        self.logger.log(logging.INFO, msg)

    def logWarning(self, msg):
        self.logger.log(logging.WARNING, msg)

    def logError(self, msg):
        self.logger.log(logging.ERROR, msg)
