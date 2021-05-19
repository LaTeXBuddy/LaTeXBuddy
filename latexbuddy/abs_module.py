"""This module defines the abstract module of LaTeXBuddy."""

from abc import ABC, abstractmethod
from enum import Enum, auto
from pathlib import Path
from typing import List

from latexbuddy.buddy import LatexBuddy
from latexbuddy.problem import Problem


class InputFileType(Enum):
    """Describes the type of input file that a module is designed to handle.

    Available options:
    - LATEX_FILE:   the unchanged LaTeX source file
    - DETEXED_FILE: the filtered LaTeX source file without any commands etc. (just text)
    """

    LATEX_FILE = auto()
    DETEXED_FILE = auto()


class Module(ABC):
    """Abstract class that defines a simple LaTeXBuddy module."""

    @abstractmethod
    def get_input_file_type(self) -> InputFileType:
        """Specifies the input file type of this module.

        :return: input file type this module is designed to check
        """
        pass

    @abstractmethod
    def run_module(self, buddy: LatexBuddy, file_path: Path) -> None:
        """Runs the checks for the respective module and collects
            errors internally.

        :param buddy: the calling LaTeXBuddy instance (for config access)
        :param file_path: path of the file to be checked
        """
        pass

    @abstractmethod
    def fetch_errors(self, buddy: LatexBuddy) -> List[Problem]:
        """Passes all currently accumulated errors to the caller.

        :param buddy: the calling LaTeXBuddy instance (for config access)
        :return: a list of all acumulated errors in this module
        """
        pass
