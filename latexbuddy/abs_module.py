"""This module defines the abstract module of LaTeXBuddy."""

from abc import ABC, abstractmethod
from typing import List

from latexbuddy import TexFile
from latexbuddy.buddy import LatexBuddy
from latexbuddy.problem import Problem


class Module(ABC):
    """Abstract class that defines a simple LaTeXBuddy module."""

    @abstractmethod
    def run_checks(self, buddy: LatexBuddy, file: TexFile) -> List[Problem]:
        """Runs the checks for the respective module and returns a list of problems
            found by the module.

        :param buddy: the calling LaTeXBuddy instance (for config access)
        :param file: LaTeX file to be checked (with built-in detex option)
        """
        pass
