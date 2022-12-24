from __future__ import annotations

from abc import ABC
from logging import DEBUG
from logging import Formatter
from logging import INFO
from logging import Logger
from logging import LogRecord
from logging import StreamHandler
from logging import WARNING
from logging.handlers import RotatingFileHandler

from colorama import Back
from colorama import Fore
from colorama import Style

from latexbuddy import __logger as root_logger
from latexbuddy import __name__ as name

_VERBOSITY_TO_LOG_LEVEL = {
    0: WARNING,
    1: INFO,
    2: DEBUG,
}

LOG_LEVEL_COLORS: dict[str, str] = {
    "DEBUG": Back.WHITE + Fore.BLACK,
    "INFO": "",
    "WARNING": Back.YELLOW + Fore.BLACK,
    "ERROR": Back.RED,
    "CRITICAL": Back.RED,
}


class ConsoleFormatter(Formatter):
    """Log formatter for console output.

    Outputs messages with colours (thanks to colorama) and severities.
    """

    def __init__(self, enable_colour: bool = True) -> None:
        super().__init__("%(message)s")
        self.colour: bool = enable_colour

    def format(self, record: LogRecord) -> str:
        if self.colour:
            level_msg = f"{LOG_LEVEL_COLORS[record.levelname]}" \
                        f"[{record.levelname}]" \
                        f"{Style.RESET_ALL}"
        else:
            level_msg = f"[{record.levelname}]"

        return f"{level_msg} {record.getMessage()}"


def __setup_root_logger(logger: Logger, verbosity: int = 0) -> None:
    """Sets up a logger.

    Intended to be used on the root logger, this module adds a file and a console
    handler with different formatters.

    :param logger: the logger to set up
    :param console_level: level of the console output
    """
    if verbosity < 0:
        raise ValueError("verbosity level cannot be negative")

    logger.name = name  # set root logger name
    logger.setLevel(DEBUG)  # output at most everything

    # reset handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)

    fh = RotatingFileHandler(
        latexbuddy.tools.get_app_dir() / "debug.log",
        maxBytes=2_097_152,  # 2 Mebibytes
        backupCount=4,
    )
    fh.setLevel(DEBUG)  # output everything to file
    fh.setFormatter(
        Formatter(
            "%(name)-30s"
            "%(relativeCreated)6d "
            "%(levelname)-8s "
            "%(message)s",
        ),
    )

    ch = StreamHandler()
    # clamp verbosity between 0 and maximum supported level (2)
    verbosity = min(verbosity, max(_VERBOSITY_TO_LOG_LEVEL))
    ch.setLevel(_VERBOSITY_TO_LOG_LEVEL[verbosity])
    ch.setFormatter(ConsoleFormatter())

    logger.addHandler(fh)
    logger.addHandler(ch)


class Loggable(ABC):
    """This class provides logging functionality to any class that inherits
    from it."""

    __logger = root_logger

    @property
    def logger(self):
        """Returns a logger that includes the full module path and the
        classname in its name."""
        return self.__logger.getChild(
            ".".join(self.__module__.split(".")[1:]),
        ).getChild(self.__class__.__name__)

    @logger.setter
    def logger(self, value: Logger) -> None:
        """Ignores any overwrite operations for property 'logger'."""
