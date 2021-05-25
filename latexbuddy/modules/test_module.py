from typing import List

from latexbuddy import TexFile
from latexbuddy.buddy import LatexBuddy
from latexbuddy.modules import Module
from latexbuddy.problem import Problem


class TestModule(Module):
    """This is a dummy module to test the module loader"""

    def __init__(self):
        """Empty constructor."""
        return

    def run_checks(self, buddy: LatexBuddy, file: TexFile) -> List[Problem]:
        """Dummy implementation that simply returns one problem without meaning.

        :param buddy: LatexBuddy instance
        :param file: file to be checked
        :return: a list of problems of length one
        """
        return [
            Problem(
                position=(0, 0),
                text="TestModule",
                checker="TestModule",
                cid="TestModule",
                file=file.tex_file,
            )
        ]


class JustSomeRandomClass:
    """This is an empty class created to test, if only Module classes are loaded"""

    def __init__(self):
        """Empty constructor"""
        pass
