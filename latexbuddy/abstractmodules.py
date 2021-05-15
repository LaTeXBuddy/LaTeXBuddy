"""This module defines the abstract module of LaTeXBuddy."""

from abc import ABC, abstractmethod


class Modules(ABC):
    """Abstract class that defines a simple LaTeXBuddy module."""

    @abstractmethod
    def run(self):
        """Runs the checks for the respective module."""
        pass


class Aspell(Modules):
    """Module for aspell.

    Aspell is a Free and Open Source spell checker developed by GNU.
    """

    def run(self, buddy, file):
        import latexbuddy.aspell as aspell

        aspell.run(buddy, file)


class Languagetool(Modules):
    """Module for LanguageTool.

    LanguageTool is a free and open-source grammar checker.
    """

    def run(self, buddy, file):
        import latexbuddy.languagetool as languagetool

        languagetool.run(buddy, file)


class Chktex(Modules):
    """Module for chktex.

    ChkTeX is a LaTeX semantic checker.
    """

    def run(self, buddy, file):
        import latexbuddy.chktex as chktex

        chktex.run(buddy, file)
