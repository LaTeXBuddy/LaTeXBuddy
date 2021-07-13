from typing import List

import latexbuddy.tools
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


class FirstDriver(Module):
    def __init__(self):
        pass

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:

        problems = [
            Problem(
                position=None,
                text="just a general problem",
                checker=FirstDriver,
                file=file.plain_file,
                severity=ProblemSeverity.ERROR
            )
        ]

        abs_pos = str(file.plain).find("This is")
        problems.append(
            Problem(
                position=file.get_position_in_tex(abs_pos),
                text="This is",
                checker=FirstDriver,
                file=file.plain_file,
                severity=ProblemSeverity.ERROR,
                description="Not an actual error, just testing the software..."
            )
        )

        return problems
