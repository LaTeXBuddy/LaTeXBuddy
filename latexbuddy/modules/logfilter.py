# LaTeXBuddy - a LaTeX checking tool
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
from __future__ import annotations

import logging
import re
from pathlib import Path
from tempfile import mkstemp

import latexbuddy.tools
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.messages import not_found
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.texfile import TexFile

LOG = logging.getLogger(__name__)

line_re = re.compile(
    r"(?P<severity>Warning|Error)\s(?P<file_path>.*)?\s?(?P<line_no>\d+):",
)


class LogFilter(Module):
    """A Filter for log files.

    Using TexFilt: https://www.ctan.org/tex-archive/support/texfilt
    """

    def __init__(self) -> None:
        """Initializes the LogFilter."""
        self.texfilt_path = Path("latexbuddy/modules/texfilt.awk")

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        """Runs the Texfilt checks on a file and returns the results as a list.

        :param config: configurations of the LaTeXBuddy instance
        :param file: the file to run checks on
        :return: a list of problems
        """
        try:
            latexbuddy.tools.find_executable("awk")
        except FileNotFoundError:
            LOG.error(not_found("awk", "AWK"))

        log_path = file.log_file
        if log_path is None:
            return []

        descriptor, raw_problems_path = mkstemp(
            prefix="latexbuddy",
            suffix="raw_log_errors",
        )
        latexbuddy.tools.execute(
            "awk",
            "-f",
            str(self.texfilt_path),
            f"{log_path} > {raw_problems_path}",
        )

        raw_problems_path = Path(raw_problems_path)
        return self.format_problems(raw_problems_path, file)

    def format_problems(
        self,
        raw_problems_path: Path,
        file: TexFile,
    ) -> list[Problem]:
        """Formats the output to a List of Problems.

        :param raw_problems_path: Path to TexFilt output
        :param file: file to check
        :return: a list of problems
        """
        problems = []
        raw_problems = raw_problems_path.read_text().split("\n\n")

        for problem_line in raw_problems:
            problem_line = problem_line.replace("\n", " ")
            match = line_re.match(problem_line)
            if not match:
                continue
            severity = match.group("severity").upper()
            file_path = file.tex_file
            # Does not work yet
            # position = (int(match.group("line_no")), 1)  # noqa

            # TODO: refactor this
            split_match = problem_line.split(f"{match.group()}")
            split = split_match[1].split("\n")
            problem_text, description = split if len(
                split,
            ) > 1 else ("", split[0])
            problems.append(
                Problem(
                    position=None,
                    text=problem_text,
                    checker=LogFilter,
                    p_type=severity,
                    file=file_path,
                    description=description,
                    category="latex",
                    key=self.display_name + "_" + severity,
                ),
            )

        return problems
