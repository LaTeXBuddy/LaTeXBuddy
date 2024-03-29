# LaTeXBuddy GNU Aspell checker
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
"""This module defines the connection between LaTeXBuddy and GNU Aspell."""
from __future__ import annotations

import logging
import subprocess
from typing import AnyStr

import latexbuddy.tools
from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from latexbuddy.texfile import TexFile

LOG = logging.getLogger(__name__)


class Aspell(Module):
    SUGGESTIONS_COUNT = 5

    def __init__(self) -> None:
        self.language: str | None = None

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        """Runs the Aspell checks on a file and returns the results as a list.

        Requires Aspell to be set up.

        :param config: the configuration options of the calling
            LaTeXBuddy instance
        :param file: LaTeX file to be checked (with built-in detex
            option)
        """

        latexbuddy.tools.find_executable("aspell", "GNU Aspell", LOG)

        supported_languages = self.find_languages()

        self.language = config.get_config_option_or_default(
            LatexBuddy,
            "language",
            "en",
            verify_type=AnyStr,  # type: ignore
            verify_choices=supported_languages,
        )

        language_country: str = config.get_config_option_or_default(
            LatexBuddy,
            "language_country",
            None,
            verify_type=AnyStr,  # type: ignore
        )

        if language_country is not None:
            language_code = f"{self.language}-{language_country}"
            if language_code in supported_languages:
                self.language = language_code

        error_list = []
        counter = 1  # counts the lines

        # execute aspell on given file and collect output
        lines = file.plain.splitlines(keepends=False)
        for line in lines:  # check every line
            if len(line) > 0:
                # the first line specifies aspell version
                out = subprocess.check_output(
                    ("aspell", "-a", "-l", self.language),  # type: ignore
                    input=line,
                    text=True,
                ).splitlines()[1:]

                if len(out) > 0:  # only if the list inst empty
                    out.pop()  # remove last element
                error_list.extend(self.format_errors(out, counter, file))

            # if there is an empty line, just increase the counter
            counter += 1

        return error_list

    @staticmethod
    def find_languages() -> list[str]:
        """Returns all languages supported by the current aspell installation.
        Omits specific language variations like 'en- variant_0'.

        :return: list of supported languages in str format
        """
        aspell_output = subprocess.check_output(
            ("aspell", "dump", "dicts"),
            text=True,
        )
        return [
            lang
            for lang in aspell_output.splitlines()
            if "-" not in lang
        ]

    def format_errors(
        self,
        out: list[str],
        line_number: int,
        file: TexFile,
    ) -> list[Problem]:
        """Parses Aspell errors and returns list of Problems.

        :param line_number: the line_number for the location
        :param out: line-split output of the aspell command
        :param file: the file path
        """
        p_type = "0"  # aspell got not error-ids
        severity = ProblemSeverity.ERROR
        key_delimiter = "_"
        problems = []

        for error in out:
            if error[0] not in ("&", "#"):
                continue

            tmp = error[1:].strip().split(": ", 1)
            if len(tmp) == 1:
                tmp.append("")
            meta_str, suggestions_str = tmp

            meta = meta_str.split(" ")
            text = meta[0]

            suggestions = []
            # & if there are suggestions
            if error[0] == "&":
                suggestions = suggestions_str.split(", ")
            # just take the first 5 suggestions
            suggestions = suggestions[:self.SUGGESTIONS_COUNT]

            # calculate the char location
            tmp_split = tmp[0].split(" ")
            if error[0] in "&":  # if there are suggestions
                char_location = int(tmp_split[2]) + 1
            else:  # if there are no suggestions
                char_location = int(tmp_split[1]) + 1

            location = file.get_position_in_tex_from_linecol(
                line_number,
                char_location,
            )
            key = "spelling" + key_delimiter + text

            problems.append(
                Problem(
                    position=location,
                    text=text,
                    checker=Aspell,
                    file=file.tex_file,
                    severity=severity,
                    p_type=p_type,
                    category="spelling",
                    suggestions=suggestions,
                    key=key,
                ),
            )
        return problems
