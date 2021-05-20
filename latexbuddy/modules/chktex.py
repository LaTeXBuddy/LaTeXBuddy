"""This module defines the connection between LaTeXBuddy and ChkTeX."""
from typing import List

import latexbuddy.buddy as ltb
import latexbuddy.tools as tools

from latexbuddy import TexFile
from latexbuddy.abs_module import Module
from latexbuddy.problem import Problem, ProblemSeverity


class ChktexModule(Module):
    def __init__(self):
        self.DELIMITER = ":"
        self.tool_name = "chktex"
        self.problem_type = "latex"

    def run_checks(self, buddy: ltb.LatexBuddy, file: TexFile) -> List[Problem]:
        """Runs the chktex checks on a file and converts them to a list of Problems

        Requires chktex to be installed seperately

        :param buddy: the LaTeXBuddy instance
        :param file: the file to run checks on
        """
        format_str = (
            self.DELIMITER.join(["%f", "%l", "%c", "%d", "%n", "%s", "%m", "%k"])
            + "\n\n"
        )
        command_output = tools.execute(
            "chktex", "-f", f"'{format_str}'", "-q", str(file.tex_file)
        )
        out_split = command_output.split("\n")
        return self.format_problems(out_split, file)

    def format_problems(self, out: List[str], file: TexFile) -> List[Problem]:
        """Converts the output of chktex to a list of Problems

        :param out: line-split output of the chktex command
        :param file: the checked file
        """
        problems = []
        key_delimiter = "_"

        for problem in out:
            out_split = problem.split(self.DELIMITER)
            if len(out_split) < 5:
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
                    position,
                    text,
                    self.tool_name,
                    str(internal_id),
                    file.tex_file,
                    severity,
                    self.problem_type,
                    description,
                    None,
                    None,
                    key,
                )
            )

        return problems
