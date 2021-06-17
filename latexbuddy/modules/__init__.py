"""This module defines the abstract class for a LaTeXBuddy module, that others can
inherit from.
"""

from abc import ABC, abstractmethod
from logging import Logger
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
    def run_checks(
        self, config: ConfigLoader, file: TexFile, logger: Logger
    ) -> List[Problem]:
        """Runs the checks and returns a list of discovered problems.

        :param config: the configuration options of the calling LaTeXBuddy instance
        :param file: LaTeX file to be checked (with built-in detex option)
        :param logger: logger capable of displaying messages with different severity
                       levels in the main LaTeXBuddy log (strongly recommended over
                       print())
        """
        pass

    def get_display_name(self) -> str:
        """This is the canonical way to determine a module's name."""

        return self.__class__.__name__


class MainModule(Module):
    """Interface class adding the ability to provide a display name to the main
    LaTeXBuddy instance.
    """

    def __init__(self):
        return

    def run_checks(
        self, config: ConfigLoader, file: TexFile, logger: Logger
    ) -> List[Problem]:
        return []
