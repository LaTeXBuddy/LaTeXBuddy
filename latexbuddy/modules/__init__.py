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
    def display_name(cls) -> str:
        """Returns the canonical display name of the module."""
        return cls.__name__


class MainModule(NamedModule):
    """Superclass intended for the main LatexBuddy instance."""


class Module(NamedModule):
    """Abstract class that defines a simple LaTeXBuddy module."""

    @abstractmethod
    def __init__(self):
        """Creates and initializes a new instance of this module."""

    @abstractmethod
    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        """Runs the checks and returns a list of discovered problems.

        :param config: the configuration options of the calling LaTeXBuddy instance
        :param file: LaTeX file to be checked (with built-in detex option)
        """
