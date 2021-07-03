"""This module defines the abstract class for a LaTeXBuddy module, that others can
inherit from.
"""

from abc import abstractmethod
from typing import List

from latexbuddy import TexFile
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.log import Loggable
from latexbuddy.problem import Problem
from latexbuddy.tools import classproperty


class NamedModule(Loggable):
    """Interface class adding the ability to provide a display name to any module
    instance.
    """

    @classproperty
    def display_name(cls) -> str:
        """Returns the canonical display name of the module."""
        return cls.__name__


class MainModule(NamedModule):
    """Superclass intended for the main LatexBuddy instance."""

    pass


class Module(NamedModule):
    """Abstract class that defines a simple LaTeXBuddy module."""

    @abstractmethod
    def __init__(self):
        """Creates and initializes a new instance of this module."""
        pass

    @abstractmethod
    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        """Runs the checks and returns a list of discovered problems.

        :param config: the configuration options of the calling LaTeXBuddy instance
        :param file: LaTeX file to be checked (with built-in detex option)
        """
        pass
