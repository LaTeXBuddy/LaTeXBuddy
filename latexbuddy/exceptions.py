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
"""This module defines standard exceptions that are to be raised when certain
application-specific errors occur."""
from __future__ import annotations


class ExecutableNotFoundError(Exception):
    """This error is raised when LaTeXBuddy can not locate a third-party
    executable dependency on the system it is running on."""


class LanguageNotSupportedError(Exception):
    """This error is raised when LaTeXBuddy or a submodule does not support the
    configured language."""


class ConfigOptionError(Exception):
    """Base Exception for errors related to loading configurations."""


class ConfigOptionNotFoundError(ConfigOptionError):
    """Describes a ConfigOptionNotFoundError.

    This error is raised when a requested config entry doesn't exist.
    """


class ConfigOptionVerificationError(ConfigOptionError):
    """Describes a ConfigOptionVerificationError.

    This error is raised when a requested config entry does not meet the
    specified criteria.
    """
