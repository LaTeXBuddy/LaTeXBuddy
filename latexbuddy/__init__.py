# LaTeXBuddy - a LaTeX checking tool
# Copyright (C) 2021-2022  LaTeXBuddy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

import logging.handlers
import sys

import latexbuddy.tools
from latexbuddy.logging_formatter import ConsoleFormatter

if sys.version_info < (3, 8):  # pragma: <3.8 cover
    from importlib_metadata import version
else:  # pragma: >=3.8 cover
    from importlib.metadata import version

# package metadata
__app_name__ = "LaTeXBuddy"  # proper name
__name__ = "latexbuddy"  # "unixified" name
__version__ = version("latexbuddy")


# by default, don't add any handler
LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())
LOG.setLevel(logging.DEBUG)

_VERBOSITY_TO_LOG_LEVEL = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}


def configure_logging(
    verbosity: int = 0,
    *,
    enable_colour: bool = True,
) -> None:
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
        _msg = "Verbosity level cannot be negative"
        raise ValueError(_msg)
    verbosity = min(verbosity, max(_VERBOSITY_TO_LOG_LEVEL))

    latexbuddy.tools.dirs.user_log_path.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        latexbuddy.tools.dirs.user_log_path / "debug.log",
        maxBytes=2_097_152,  # 2 Mebibytes
        backupCount=4,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(name)-30s %(levelname)-8s %(message)s",
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
