from abc import ABC
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, Formatter, Logger, LogRecord
from logging.handlers import RotatingFileHandler

from colorama import Back, Fore, Style
from double_stream_handler import DoubleStreamHandler

import latexbuddy

from latexbuddy import __logger as root_logger
from latexbuddy import __name__ as name


class ConsoleFormatter(Formatter):
    """Log formatter for console output.

    Outputs messages with colours (thanks to colorama) and severities.
    """

    def __init__(self, enable_colour: bool = True) -> None:
        super().__init__("%(message)s")
        self.colour: bool = enable_colour

    def format(self, record: LogRecord) -> str:
        level = record.levelno
        prefix = ""

        if level < INFO:
            if self.colour:
                prefix += Fore.LIGHTBLACK_EX
        elif WARNING <= level < ERROR:
            if self.colour:
                prefix += Style.BRIGHT + Fore.YELLOW
            prefix += "Warning: "
        elif ERROR <= level < CRITICAL:
            if self.colour:
                prefix += Style.BRIGHT + Fore.RED
            prefix += "Error: "
        elif CRITICAL <= level:
            if self.colour:
                prefix += Back.RED + Fore.BLACK
            prefix += "FATAL ERROR: "

        return prefix + super().format(record) + Style.RESET_ALL


def __setup_root_logger(logger: Logger, console_level: int = INFO) -> None:
    """Sets up a logger.

    Intended to be used on the root logger, this module adds a file and a console
    handler with different formatters.

    :param logger: the logger to set up
    :param console_level: level of the console output
    """
    logger.name = name  # set root logger name
    logger.setLevel(DEBUG)  # output at most everything

    # reset handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)

    fh = RotatingFileHandler(
        latexbuddy.tools.get_app_dir() / "debug.log", maxBytes=4000000, backupCount=8
    )
    fh.setLevel(DEBUG)  # output everything to file
    fh.setFormatter(
        Formatter(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s "
            "%(filename)s:%(lineno)d "
            "%(funcName)s() "
            "%(message)s"
        )
    )

    ch = DoubleStreamHandler()
    ch.setLevel(console_level)
    ch.setFormatter(ConsoleFormatter())

    logger.addHandler(fh)
    logger.addHandler(ch)


class Loggable(ABC):
    """
    This class provides logging functionality to any class that inherits from it.
    """

    __logger = root_logger

    @property
    def logger(self):
        """
        Returns a logger that includes the full module path and the classname in
        its name.
        """
        return self.__logger.getChild(
            ".".join(self.__module__.split(".")[1:])
        ).getChild(self.__class__.__name__)

    @logger.setter
    def logger(self, value: Logger) -> None:
        """Ignores any overwrite operations for property 'logger'."""
        pass
