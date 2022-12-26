# LaTeXBuddy - a LaTeX checking tool
# Copyright (C) 2022  LaTeXBuddy
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
"""This module hosts :py:mod:`logging` formatters."""
from __future__ import annotations

import logging

from latexbuddy import colour

LOG_LEVEL_COLORS: dict[str, str] = {
    "DEBUG": colour.BLACK_ON_WHITE,
    "INFO": "",
    "WARNING": colour.BLACK_ON_YELLOW,
    "ERROR": colour.ON_RED,
    "CRITICAL": colour.ON_RED,
}


class ConsoleFormatter(logging.Formatter):
    """Log formatter for console output.

    This formatter outputs the severity, written with a respective
    colour, ans the message itself.
    """

    def __init__(self, *, enable_colour: bool = True) -> None:
        super().__init__("%(message)s")
        self.colour: bool = enable_colour

    def format(self, record: logging.LogRecord) -> str:
        if self.colour:
            level_msg = f"{LOG_LEVEL_COLORS[record.levelname]}" \
                        f"[{record.levelname}]" \
                        f"{colour.RESET_ALL}"
        else:
            level_msg = f"[{record.levelname}]"

        return f"{level_msg} {super().format(record)}"
