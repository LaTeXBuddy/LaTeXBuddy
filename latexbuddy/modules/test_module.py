from typing import List

from latexbuddy import TexFile
from latexbuddy.abs_module import Module
from latexbuddy.buddy import LatexBuddy
from latexbuddy.problem import Problem


class TestModule(Module):
    def __init__(self):
        return

    def run_checks(self, buddy: LatexBuddy, file: TexFile) -> List[Problem]:
        return [
            Problem(
                (0, 0),
                "TestModule",
                "TestModule",
                "TestModule",
                file.path,
            )
        ]


class JustSomeRandomClass:
    def __init__(self):
        pass
