"""This module defines the abstract module of LaTeXBuddy."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from latexbuddy.error_class import Error
from latexbuddy.latexbuddy import LatexBuddy


class Module(ABC):
    """Abstract class that defines a simple LaTeXBuddy module."""

    @abstractmethod
    def run_module(self, buddy: LatexBuddy, file_path: Path) -> None:
        """Runs the checks for the respective module and collects
            errors internally.

        :param buddy: the calling LaTeXBuddy instance (for config access)
        :param file_path: path of the file to be checked
        """
        pass

    @abstractmethod
    def get_errors(self, buddy: LatexBuddy) -> List[Error]:
        """Passes all currently accumulated errors to the caller.

        :param buddy: the calling LaTeXBuddy instance (for config access)
        :return: a list of all acumulated errors in this module
        """
        pass
