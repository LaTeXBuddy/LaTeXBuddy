"""This module defines the abstract class for a LaTeXBuddy module, that others can
inherit from.
"""

from abc import ABC, abstractmethod
from typing import List

from latexbuddy import TexFile
from latexbuddy.buddy import LatexBuddy
from latexbuddy.problem import Problem


class Module(ABC):
    """Abstract class that defines a simple LaTeXBuddy module."""

    @abstractmethod
    def __init__(self):
        """Creates and initializes a new instance of this module."""
        pass

    @abstractmethod
    def run_checks(self, buddy: LatexBuddy, file: TexFile) -> List[Problem]:
        """Runs the checks and returns a list of discovered problems.

        # TODO: vllt einfach selbst Config nehmen statt des "dicken" buddy-Attributes?
        :param buddy: the calling LaTeXBuddy instance (for config access)
        :param file: LaTeX file to be checked (with built-in detex option)
        """
        pass
