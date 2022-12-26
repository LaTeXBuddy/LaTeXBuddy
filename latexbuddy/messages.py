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
"""This module defines standard messages that are to be printed to the command
line as well as builders for those."""
from __future__ import annotations

from pathlib import Path


def not_found(executable: str, to_install: str) -> str:
    # importing this here to avoid circular import error
    from latexbuddy import __app_name__

    return (
        f"'{executable}' not found! "
        f"Make sure you've installed {to_install} correctly. "
        f"Refer to the {__app_name__} manual for help."
    )


def error_occurred_in_module(module_name: str) -> str:
    return (
        f"An error occurred while executing checks for module '{module_name}'."
        f" Executions was stopped, no results generated."
    )


def texfile_error(msg: str) -> str:
    return f"An error occurred while compiling the tex file:" f"{msg}"


def path_not_found(error_occasion: str, path: Path) -> str:
    return (
        f"An error occurred during {error_occasion}: "
        f"No such file or directory: {str(path)}."
    )
