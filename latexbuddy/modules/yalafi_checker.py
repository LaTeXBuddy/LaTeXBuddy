from __future__ import annotations

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from latexbuddy.texfile import TexFile


class YaLafi(Module):
    def __init__(self):
        pass

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:

        problems = []

        if file.is_faulty:
            for raw_err in file._parse_problems:

                problems.append(
                    Problem(
                        position=raw_err[0],
                        text=raw_err[1],
                        checker=YaLafi,
                        p_type="tex2txt",
                        file=file.tex_file,
                        severity=ProblemSeverity.ERROR,
                        category="latex",
                        key=self.display_name + "_tex2txt",
                    ),
                )

        return problems
