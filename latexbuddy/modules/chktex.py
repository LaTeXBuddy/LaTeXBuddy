"""This module defines the connection between LaTeXBuddy and ChkTeX.

ChkTeX Documentation: https://www.nongnu.org/chktex/ChkTeX.pdf
"""
import os

from typing import List

import latexbuddy.tools as tools

from latexbuddy import TexFile
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity


class Chktex(Module):
    def __init__(self):
        self.DELIMITER = ":::"
        self.tool_name = "chktex"
        self.problem_type = "latex"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        """Runs the chktex checks on a file and converts them to a list of Problems

        Requires chktex to be installed separately

        :param config: the configuration options of the calling LaTeXBuddy instance
        :param file: LaTeX file to be checked (with built-in detex option)
        """

        tools.find_executable("chktex", "ChkTeX", self.logger)

        format_str = (
            self.DELIMITER.join(
                ["%f", "%l", "%c", "%d", "%n", "%s", "%m", "%k", "%r", "%t"]
            )
            + "\n\n"
        )

        dir_path, file_path = os.path.split(os.path.abspath(str(file.tex_file)))
        command_output = tools.execute(
            "cd", dir_path, ";", "chktex", "-f", f"'{format_str}'", "-q", file_path
        )
        out_split = command_output.split("\n")

        result = self.format_problems(out_split, file)

        return result

    def format_problems(self, out: List[str], file: TexFile) -> List[Problem]:
        """Converts the output of chktex to a list of Problems

        :param out: line-split output of the chktex command
        :param file: the checked file
        """
        problems = []
        key_delimiter = "_"

        for problem in out:
            out_split = problem.split(self.DELIMITER)
            if len(out_split) < 10:
                continue
            severity = (
                ProblemSeverity.WARNING
                if out_split[7] == "Warning"
                else ProblemSeverity.ERROR
            )
            row = int(out_split[1])
            col = int(out_split[2])
            length = int(out_split[3])  # not used for now
            internal_id = out_split[4]
            text = out_split[5]
            description = out_split[6] if len(out_split[6]) > 0 else None
            position = (row, col)
            key = self.tool_name + key_delimiter + str(internal_id)

            problems.append(
                Problem(
                    position=position,
                    text=text,
                    checker=Chktex,
                    p_type=str(internal_id),
                    file=file.tex_file,
                    severity=severity,
                    category=self.problem_type,
                    description=description,
                    key=key,
                    context=(out_split[8], out_split[9]),
                )
            )

        return problems
