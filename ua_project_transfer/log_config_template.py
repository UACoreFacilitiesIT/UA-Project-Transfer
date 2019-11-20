import logging
from datetime import datetime


class FileFormatter(logging.Filter):
    """Returns the passed-in formatter to use based on record level."""
    def __init__(self, level_formatters):
        self._level_formatters = level_formatters

    def format(self, record):
        formatter = self._level_formatters.get(record.levelno)
        return formatter.format(record)


class LevelFilter(object):
    """Restricts handler to trigger only the levels specified."""
    def __init__(self, levels):
        self.__levels = levels

    def filter(self, log_record):
        if log_record.levelno in self.__levels:
            return True
        else:
            return False


CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "file_formatter": {
            "()": FileFormatter,
            "level_formatters": {
                logging.INFO: logging.Formatter(
                    fmt=(
                        "%(levelname)s: Successfully transferred project:"
                        " %(message)s")),
                logging.ERROR: logging.Formatter(
                    fmt=(
                        "%(levelname)s: Could not transfer project:"
                        " %(message)s"))
            }
        },
    },
    "handlers": {
        "file_handler": {
            "class": "logging.FileHandler",
            "filename": f"project_transfer_log_{datetime.today().year}.txt",
            # Open in append mode to not delete all the previous transfers.
            "mode": "a",
            "formatter": "file_formatter",
            "filters": ["file_filter"],
        },
        "null_handler": {
            "class": "logging.NullHandler",
            "filters": ["null_filter"],
        }
    },
    "filters": {
        "file_filter": {
            "()": LevelFilter,
            "levels": [logging.INFO, logging.ERROR]
        },
        "null_filter": {
            "()": LevelFilter,
            "levels": [logging.WARNING, logging.CRITICAL]
        }
    },
    "loggers": {
        "__main__": {
            "propogate": False,
            "level": logging.DEBUG,
            "handlers": [
                "file_handler",
            ]
        },
        "__main__.next_steps": {
            "propogate": True,
            "level": logging.DEBUG,
            "handlers": ["null_handler"]
        },
        "__main__.project_lims_tools": {
            "propogate": True,
            "level": logging.DEBUG,
            "handlers": ["null_handler"]
        },
    }
}
