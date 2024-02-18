import logging
import os


def get_logging_config():
    """
        Reads the environment variables and returns a tuple: log_enabled, log_file, log_level. The first is a bool
        indicating whether the logging is enabled at all, the second is a log level for the python's logging library.
    """

    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    log_level = log_level_map.get(os.getenv('LOG_LEVEL'), logging.INFO)

    return log_enabled, log_level
