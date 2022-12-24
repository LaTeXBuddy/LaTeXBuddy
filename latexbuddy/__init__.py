from __future__ import annotations

import logging.handlers
from pkgutil import extend_path

import latexbuddy.tools
from latexbuddy import colour
from latexbuddy.logging_formatter import ConsoleFormatter

# package metadata
__app_name__ = "LaTeXBuddy"  # proper name
__name__ = "latexbuddy"  # "unixified" name
__path__ = extend_path(__path__, __name__)
__version__ = "0.4.1"


# by default, don't add any handler
LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())
LOG.setLevel(logging.DEBUG)

_VERBOSITY_TO_LOG_LEVEL = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}


def configure_logging(verbosity: int = 0, enable_colour: bool = True) -> None:
    """Configures :py:mod:`logging`.

    This method adds the correct :py:class:`logging.Handler`s and
    :py:class:`logging.Formatter`s to the root logger. By default,
    the logger will accept messages of all severities and output them
    to a file. Additionally, it will also output warnings and errors
    to the console.

    :param verbosity: how verbose the console output should be.
                       0 (default) will output just warnings and errors,
                       1 will also output info messages,
                       2 will output all messages
    :param enable_colour: whether to make the output coloured
    """
    if verbosity < 0:
        raise ValueError("verbosity level cannot be negative")
    verbosity = min(verbosity, max(_VERBOSITY_TO_LOG_LEVEL))

    file_handler = logging.handlers.RotatingFileHandler(
        latexbuddy.tools.get_app_dir() / "debug.log",
        maxBytes=2_097_152,  # 2 Mebibytes
        backupCount=4,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(name)-30s %(relativeCreated)6d %(levelname)-8s %(message)s",
        ),
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(_VERBOSITY_TO_LOG_LEVEL[verbosity])
    console_handler.setFormatter(ConsoleFormatter(enable_colour=enable_colour))

    LOG.addHandler(file_handler)
    LOG.addHandler(console_handler)
    LOG.debug(f"Added handlers to logger root at `{__name__}`")


try:
    from colorama import just_fix_windows_console

    just_fix_windows_console()
except ModuleNotFoundError:
    LOG.debug("colorama not found, we are not on Windows")
except ImportError:
    LOG.debug("Old colorama version installed, using legacy init")
    import colorama
    colorama.init()
