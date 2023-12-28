# LaTeXBuddy Diction checker
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

import hashlib
import logging
import os
import subprocess
from pathlib import Path
from typing import AnyStr

from unidecode import unidecode

import latexbuddy.tools
from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from latexbuddy.texfile import TexFile

LOG = logging.getLogger(__name__)


class Diction(Module):
    __SUPPORTED_LANGUAGES = ["en", "de", "nl"]

    def __init__(self) -> None:
        self.language = None

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        # check, if diction is installed
        latexbuddy.tools.find_executable("diction", "Diction", LOG)

        self.language = config.get_config_option_or_default(
            LatexBuddy,
            "language",
            None,
            verify_type=AnyStr,  # type: ignore
            verify_choices=Diction.__SUPPORTED_LANGUAGES,
        )

        # replace umlauts so error position is correct
        lines = Path(file.plain_file).read_text()
        original_lines = lines.splitlines(keepends=True)

        lines = unidecode(lines)

        # write cleaned text to tempfile
        cleaned_file = Path(file.plain_file).with_suffix(".cleaned")
        cleaned_file.write_text(lines)

        # execute diction and collect output
        diction_output = subprocess.check_output(
            (
                "diction",
                "--suggest",
                "--language",
                self.language,  # type: ignore
                cleaned_file,
            ),
            text=True,
        )

        # remove unnecessary information and split lines
        errors = diction_output.splitlines()[:-2]

        # remove empty lines
        cleaned_errors = []
        for error in errors:
            if len(error) > 0:  # remove empty lines
                cleaned_errors.append(error.strip())

        # remove temp file
        os.remove(cleaned_file)

        # return list of Problems
        return self.format_errors(
            cleaned_errors,
            original_lines,
            file,
        )

    @staticmethod
    def _format_one_double_world_error(
        error: str,
        original: list[str],
    ) -> tuple[str, tuple[int, int], str]:
        o_line = ""

        # FIXME: This may return less items
        src, lines, chars, sugg = error.split(":", maxsplit=3)
        split_lines = lines.split("-")
        split_chars = chars.split("-")
        split_lines_int = [int(a) for a in split_lines]
        split_chars_int = [int(a) for a in split_chars]
        start_line, end_line = split_lines_int[0:1]
        start_char, end_char = split_chars_int[0:1]
        start_char -= 1  # zero-index chars
        if start_line == end_line:
            o_line = original[start_line - 1][start_char:end_char]
        else:
            for x in range(start_line, end_line + 1):
                if x == end_line:
                    o_line += original[x - 1][:end_char]
                    continue
                if x == start_line:
                    o_line += original[x - 1][start_char:]
                    continue
                o_line += original[x - 1]
        location = (start_line, start_char)

        return o_line, location, sugg

    @staticmethod
    def _format_one_regular_error(
        error: str,
        original: list[str],
        file: TexFile,
    ) -> tuple[str, tuple[int, int], str]:
        o_line = ""

        src, location, sugg = error.split(":", maxsplit=2)
        start_line = int(location.split(".")[0])
        start_char = int(location.split(".")[1].split("-")[0])
        end_line = int(location.split("-")[1].split(".")[0])
        end_char = int(location.split("-")[1].split(".")[1])
        if start_line == end_line:
            o_line = original[start_line - 1][start_char - 1: end_char]
        else:
            for x in range(start_line, end_line + 1):
                if x == end_line:
                    o_line += original[x - 1][:end_char]
                    continue
                if x == start_line:
                    o_line += original[x - 1][start_char:]
                    continue
                o_line += original[x - 1]
        location = file.get_position_in_tex_from_linecol(
            start_line,
            start_char,
        )

        return o_line, location, sugg

    def _format_one_error(
        self,
        error: str,
        original: list[str],
        file: TexFile,
    ) -> Problem:
        o_line = ""

        split_error = error.split(" ")
        double_world = False

        for i in range(0, len(split_error)):
            if split_error[i] == "->":
                if i == len(split_error) - 2:
                    break
                if split_error[i + 1] == "Double":
                    double_world = True
                else:
                    break

        if double_world:
            o_line, location, sugg = self._format_one_double_world_error(
                error,
                original,
            )

        else:
            o_line, location, sugg = self._format_one_regular_error(
                error,
                original,
                file,
            )

        line_hash = hashlib.sha1(
            o_line.encode(),
            usedforsecurity=False,
        ).hexdigest()

        return Problem(
            position=location,
            text=o_line,
            checker=Diction,
            p_type="0",
            file=file.plain_file,
            severity=ProblemSeverity.WARNING,
            category="grammar",
            suggestions=[sugg],
            key=f"{self.display_name}_{line_hash}",
        )

    def format_errors(
        self,
        out: list[str],
        original: list[str],
        file: TexFile,
    ) -> list[Problem]:
        """Parses diction errors and returns list of Problems.

        :param original: lines of file to check as list
        :param out: line split output of the diction command with empty
                    lines removed
        :param file: the ``TexFile`` instance
        """
        problems = []
        for error in out:
            problems.append(
                self._format_one_error(error, original, file),
            )

        return problems
