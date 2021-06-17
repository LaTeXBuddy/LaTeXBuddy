"""This module defines the abstract class for a LaTeXBuddy module, that others can
inherit from.
"""

from abc import ABC, abstractmethod
from typing import List

from latexbuddy import TexFile
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.problem import Problem


class Module(ABC):
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

    def get_display_name(self) -> str:
        """This is the canonical way to determine a module's name."""

        return self.__class__.__name__
