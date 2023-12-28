# LaTeXBuddy ChkTeX checker
# Copyright (C) 2021-2022  LaTeXBuddy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""This module defines the connection between LaTeXBuddy and ChkTeX.

ChkTeX Documentation: https://www.nongnu.org/chktex/ChkTeX.pdf
"""
from __future__ import annotations

import logging
import subprocess

import latexbuddy.tools
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from latexbuddy.texfile import TexFile

LOG = logging.getLogger(__name__)


class Chktex(Module):
    def __init__(self) -> None:
        self.DELIMITER = ":::"
        self.problem_type = "latex"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        """Runs the chktex checks on a file and converts them to a list of
        Problems.

        Requires chktex to be installed separately

        :param config: the configuration options of the calling
            LaTeXBuddy instance
        :param file: LaTeX file to be checked (with built-in detex
            option)
        """

        latexbuddy.tools.find_executable("chktex", "ChkTeX", LOG)

        format_str = (
            ":::".join(
                ["%f", "%l", "%c", "%d", "%n", "%s", "%m", "%k", "%r", "%t"],
            )
            + "\n\n"
        )

        file_path = str(file.tex_file)

        chktex_output = subprocess.check_output(
            (
                "chktex",
                "-f",
                format_str,
                "-q",
                file_path,
            ),
            text=True,
        )

        return self.format_problems(chktex_output.splitlines(), file)

    def format_problems(self, out: list[str], file: TexFile) -> list[Problem]:
        """Converts the output of chktex to a list of Problems.

        :param out: line-split output of the chktex command
        :param file: the checked file
        """
        problems = []
        key_delimiter = "_"

        for problem in out:
            out_split = problem.split(self.DELIMITER)

            # Sometimes ChkTeX gives us less segments back
            # TODO: fix this more elegantly
            if len(out_split) < 10:  # noqa: PLR2004
                continue

            severity = (
                ProblemSeverity.WARNING
                if out_split[7] == "Warning"
                else ProblemSeverity.ERROR
            )
            row = int(out_split[1])
            col = int(out_split[2])
            # length = int(out_split[3])  # noqa not used for now
            internal_id = out_split[4]
            text = out_split[5]
            description = out_split[6] if len(out_split[6]) > 0 else ""
            position: tuple[int, int] | None = (row, col)
            key = self.display_name + key_delimiter + str(internal_id)

            # convert problems with text-length of zero to general problems
            if len(text) < 1:
                position = None
                description += f" (in file {str(file)})"

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
                ),
            )

        return problems
