"""This module defines the abstract class for a LaTeXBuddy module, that others can
inherit from.
"""

from abc import ABC, abstractmethod
from logging import Logger
from typing import List

from latexbuddy import TexFile
from latexbuddy import __logger as root_logger
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.problem import Problem
from latexbuddy.tools import classproperty


class NamedModule(ABC):
    """Interface class adding the ability to provide a display name to any module
    instance.
    """

    @classproperty
    def display_name(cls) -> str:
        """Returns the canonical display name of the module."""
        return cls.__name__

    @display_name.setter
    def display_name(cls, value: str) -> None:
        """Ignores any overwrite operations for property 'display_name'."""
        pass


class MainModule(NamedModule):

    __logger = root_logger.getChild("buddy")

    @property
    def logger(self):
        return self.__logger.getChild(self.display_name)

    @logger.setter
    def logger(self, value: Logger) -> None:
        """Ignores any overwrite operations for property 'logger'."""
        pass


class Module(NamedModule):
    """Abstract class that defines a simple LaTeXBuddy module."""

    __logger = root_logger.getChild("modules")

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

    @property
    def logger(self) -> Logger:
        """Returns the logger of the module as a child of LaTeXBuddy's root_logger."""
        return self.__logger.getChild(self.display_name)

    @logger.setter
    def logger(self, value: Logger) -> None:
        """Ignores any overwrite operations for property 'logger'."""
        pass
