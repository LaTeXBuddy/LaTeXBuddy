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
"""This module defines the abstract class for a LaTeXBuddy module, that others
can inherit from."""
from __future__ import annotations

from abc import abstractmethod

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.problem import Problem
from latexbuddy.texfile import TexFile
from latexbuddy.tools import classproperty


class NamedModule:
    """Interface class adding the ability to provide a display name to any
    module instance."""

    @classproperty
    def display_name(cls) -> str:  # noqa
        """Returns the canonical display name of the module."""
        return cls.__name__  # type: ignore


class MainModule(NamedModule):
    """Superclass intended for the main LatexBuddy instance."""


class Module(NamedModule):
    """Abstract class that defines a simple LaTeXBuddy module."""

    @abstractmethod
    def __init__(self) -> None:
        """Creates and initializes a new instance of this module."""

    @abstractmethod
    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        """Runs the checks and returns a list of discovered problems.

        :param config: the configuration options of the calling
                       LaTeXBuddy instance
        :param file: LaTeX file to be checked (with built-in detex
                     option)
        """
