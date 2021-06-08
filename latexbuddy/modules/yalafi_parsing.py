from typing import List

from latexbuddy import TexFile
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity


class YaLafi(Module):
    def __init__(self):
        pass

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:

        problems = []

        if file.is_faulty:
            for raw_err in file._parse_problems:

                problems.append(
                    Problem(
                        position=raw_err[0],
                        text=raw_err[1],
                        checker="YaLafi",
                        cid="tex2txt",
                        file=file.tex_file,
                        severity=ProblemSeverity.ERROR,
                        category="latex",
                    )
                )

        return problems
