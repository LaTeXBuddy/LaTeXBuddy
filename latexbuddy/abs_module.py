"""This module defines the abstract module of LaTeXBuddy."""

from abc import ABC, abstractmethod


class Module(ABC):
    """Abstract class that defines a simple LaTeXBuddy module."""

    @abstractmethod
    def run_module(self, buddy, file_path):
        """Runs the checks for the respective module."""
        pass

    # TODO: define attributes for method
    @abstractmethod
    def save_errors(self):
        """Saves the Errors into the error_class"""
        pass
