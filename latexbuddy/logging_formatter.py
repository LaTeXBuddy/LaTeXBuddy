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
