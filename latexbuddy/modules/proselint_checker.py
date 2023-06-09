# LaTeXBuddy proselint checker
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
from typing import Any

from proselint.tools import lint

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from latexbuddy.texfile import TexFile

LOG = logging.getLogger(__name__)


class ProseLint(Module):
    def __init__(self) -> None:
        self.problem_type = "grammar"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        lang = config.get_config_option_or_default(
            LatexBuddy, "language", None,
        )

        if lang != "en":
            LOG.info(
                "Proselint only supports documents written in English.",
            )
            return []

        suggestions = lint(file.plain)

        return self.format_errors(suggestions, file)

    def format_errors(
        self,
        suggestions: list[tuple[str, str, int, int, int, int, int, str, Any]],
        file: TexFile,
    ) -> list[Problem]:
        problems = []
        for suggestion in suggestions:
            p_type = suggestion[0]
            description = suggestion[1]
            # line, col = (suggestion[2] + 1, suggestion[3] + 1)  # noqa
            start_char = suggestion[4] - 1
            position = file.get_position_in_tex(start_char)
            length = suggestion[6]
            text = self.get_text(start_char, length, file)
            severity_map = {
                "warning": ProblemSeverity.WARNING,
                "error": ProblemSeverity.ERROR,
                "suggestion": ProblemSeverity.INFO,
            }
            severity = severity_map[suggestion[7]]
            replacements = suggestion[8]
            if replacements is None:
                replacements = []
            delimiter = "_"
            key = self.display_name + delimiter + p_type
            problems.append(
                Problem(
                    position=position,
                    text=text,
                    checker=ProseLint,
                    p_type=p_type,
                    file=file.tex_file,
                    severity=severity,
                    category=self.problem_type,
                    description=description,
                    suggestions=replacements,
                    key=key,
                    length=length,
                ),
            )
        return problems

    @staticmethod
    def get_text(start_char: int, length: int, file: TexFile) -> str:
        text = file.plain
        return text[start_char: start_char + length]
