# LaTeXBuddy various in-house checkers
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

import os
import re

import latexbuddy.tools
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from latexbuddy.texfile import TexFile


class UnreferencedFigures(Module):
    def __init__(self) -> None:
        self.p_type = "0"
        self.severity = ProblemSeverity.INFO
        self.category = "latex"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        """Finds unreferenced figures.

        :param config: the configuration options of the calling
            LaTeXBuddy instance
        :param file: LaTeX file to be checked (with built-in detex
            option)
        :return: a list of found problems
        """
        tex = file.tex
        problems = []
        pattern = r"\\begin{figure}[\w\W]*?\\end{figure}"
        figures = re.finditer(pattern, tex)
        labels = {}

        for figure_match in figures:
            start, end = figure_match.span()
            length = end - start
            split = figure_match.group(0).split("\\")
            for word in split:
                label_match = re.search(
                    re.escape("label{") + "(.*)" + re.escape("}"),
                    word,
                )
                if label_match is not None:
                    label = label_match.group(1)
                    labels[(start, length)] = label

        for (position, length), label in labels.items():
            line, col, offset = latexbuddy.tools.absolute_to_linecol(
                file.tex,
                position,
            )
            if re.search(r"\\c?ref{" + label + re.escape("}"), tex) is None:
                problems.append(
                    Problem(
                        position=(line, col),
                        text=label,
                        checker=UnreferencedFigures,
                        category=self.category,
                        p_type=self.p_type,
                        file=file.tex_file,
                        severity=self.severity,
                        description=f"Figure {label} not referenced.",
                        key=self.display_name + "_" + label,
                        length=length,
                        context=("\\label{", "}"),
                    ),
                )

        return problems


class SiUnitx(Module):
    def __init__(self) -> None:
        self.category = "latex"
        self.severity = ProblemSeverity.INFO

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        """Finds units and long numbers used without siunitx package.

        :param: config: configurations of the buddy instance :param:
        file:
        :param: config: configurations of the buddy instance
        :param: file: the file to check
        :return: a list of found problems
        """
        problems = []
        for problem in self.find_long_numbers(file):
            problems.append(problem)
        for problem in self.find_units(file):
            problems.append(problem)
        return problems

    def find_long_numbers(self, file: TexFile) -> list[Problem]:
        """Finds long numbers used without siunitx package.

        :param: file: the file to check
        :return: a list of found problems
        """
        problems = []
        text = file.tex
        all_numbers = re.finditer("[0-9]+", text)
        threshold = 3

        def filter_big_numbers(n: re.Match[str]) -> bool:
            return len(n.group(0)) > threshold

        numbers = list(filter(filter_big_numbers, all_numbers))

        for number_match in numbers:
            start, end = number_match.span()
            length = end - start
            line, col, offset = latexbuddy.tools.absolute_to_linecol(
                text, start,
            )
            problems.append(
                Problem(
                    position=(line, col),
                    text=number_match.group(0),
                    checker=SiUnitx,
                    category=self.category,
                    p_type="num",
                    file=file.tex_file,
                    severity=self.severity,
                    description=(
                        f"For number {number_match.group(0)}, "
                        R"\num from siunitx may be used."
                    ),
                    key=self.display_name + "_" + number_match.group(0),
                    length=length,
                ),
            )
        return problems

    def find_units(self, file: TexFile) -> list[Problem]:
        """Finds units used without siunitx package.

        :param: file: the file to check
        :return: a list of found problems
        """
        problems = []
        units = [
            "A",
            "cd",
            "K",
            "kg",
            "m",
            "mol",
            "s",
            "C",
            "F",
            "Gy",
            "Hz",
            "H",
            "J",
            "lm",
            "kat",
            "lx",
            "N",
            "Pa",
            "rad",
            "S",
            "Sv",
            "sr",
            "T",
            "V",
            "W",
            "Wb",
            "au",
            "B",
            "Da",
            "d",
            "dB",
            "eV",
            "ha",
            "h",
            "L",
            "min",
            "Np",
            "t",
        ]
        prefixes = [
            "y",
            "z",
            "a",
            "f",
            "p",
            "n",
            "m",
            "c",
            "d",
            "da",
            "h",
            "k",
            "M",
            "G",
            "T",
            "P",
            "E",
            "Z",
            "Y",
        ]
        text = file.tex
        units_cp = units.copy()
        for unit in units:
            for prefix in prefixes:
                units_cp.append(prefix + unit)

        units = units_cp.copy()

        used_units = []
        for unit in units:
            pattern = rf"[0-9]+\s*{unit}\s"
            used_unit = re.finditer(pattern, text)
            used_units.append(used_unit)

        for used_unit in used_units:
            for unit_match in used_unit:
                start, end = unit_match.span()
                length = end - start
                line, col, offset = latexbuddy.tools.absolute_to_linecol(
                    text, start,
                )
                problems.append(
                    Problem(
                        position=(line, col),
                        text=unit_match.group(0),
                        checker=SiUnitx,
                        category=self.category,
                        p_type="unit",
                        file=file.tex_file,
                        severity=self.severity,
                        description=(
                            f"For unit {unit_match.group(0)}, "
                            "siunitx may be used."
                        ),
                        key=self.display_name + "_" + unit_match.group(0),
                        length=length,
                    ),
                )

        return problems


class EmptySections(Module):
    def __init__(self) -> None:
        self.category = "latex"
        self.severity = ProblemSeverity.INFO

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        tex = file.tex
        problems = []
        pattern = r"\\section{(.*)}\s+\\subsection"
        empty_sections = re.finditer(pattern, tex)
        for section_match in empty_sections:
            start, end = section_match.span()
            length = end - start
            line, col, offset = latexbuddy.tools.absolute_to_linecol(
                tex, start,
            )
            text = section_match.group(1)
            problems.append(
                Problem(
                    position=(line, col),
                    text=text,
                    checker=EmptySections,
                    category=self.category,
                    p_type="0",
                    file=file.tex_file,
                    severity=self.severity,
                    description="Sections may not be empty.",
                    key=self.display_name + "_" + text,
                    length=length,
                    context=("\\section{", "}"),
                ),
            )
        return problems


class URLCheck(Module):
    def __init__(self) -> None:
        self.category = "latex"
        self.severity = ProblemSeverity.INFO

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        tex = file.tex
        problems = []
        # https://stackoverflow.com/q/6038061
        pattern = r"(http|ftp|https)(:\/\/)" \
                  r"([\w_-]+(?:(?:\.[\w_-]+)+))" \
                  r"([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
        urls = re.finditer(pattern, tex)

        for url_match in urls:

            start, end = url_match.span()
            length = end - start
            command_len = len("\\url{")
            if tex[start - command_len: start] == "\\url{":
                continue
            line, col, offset = latexbuddy.tools.absolute_to_linecol(
                tex, start,
            )
            problems.append(
                Problem(
                    position=(line, col),
                    text=url_match.group(0),
                    checker=URLCheck,
                    category=self.category,
                    p_type="0",
                    file=file.tex_file,
                    severity=self.severity,
                    description="For URLs, use \\url.",
                    key=self.display_name + "_" + url_match.group(0),
                    length=length,
                ),
            )
        return problems


class CheckFigureResolution(Module):
    file_endings = [
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".jpg",
        ".jpeg",
        ".jpe",
        ".jif",
        ".jfif",
        ".jfi",
        ".gif",
        ".webp",
        ".tiff",
        ".tif",
        ".psd",
        ".dip",
        ".heif",
        ".heic",
        ".jp2",
    ]

    def __init__(self) -> None:
        self.p_type = "0"
        self.severity = ProblemSeverity.INFO
        self.category = "latex"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        """Finds potential low resolution figures.

        :param: config: configurations of the buddy instance :param:
        file:
        :param: config: configurations of the buddy instance
        :param: file: the file to check
        :return: a list of found problems
        """
        search_root = os.path.dirname(file.tex_file)
        problems = []
        figures: list[str] = []

        for root, _dirs, files in os.walk(search_root):
            root_name = os.path.basename(root)
            for current_file in files:
                name, ending = os.path.splitext(current_file)
                if ending.lower() not in self.file_endings:
                    if root_name.lower() != figures:
                        continue
                    if ending.lower() != ".pdf":
                        continue

                figures.append(current_file)
                problems.append(
                    Problem(
                        position=None,
                        text=name,
                        checker=CheckFigureResolution,
                        category=self.category,
                        p_type="0",
                        file=file.tex_file,
                        severity=self.severity,
                        description=(
                            "Figure might have low resolution due "
                            f"to its file format: {ending}"
                        ),
                        key=self.display_name + "_" + current_file,
                        length=1,
                    ),
                )

        return problems


class NativeUseOfRef(Module):
    def __init__(self) -> None:
        self.severity = ProblemSeverity.INFO
        self.category = "latex"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        description = "Instead of \\ref{} use a more precise command, " \
                      "for example, \\cref{}"
        tex = file.tex
        problems = []
        ref_pattern = "\\ref{"

        curr_problem_start = tex.find(ref_pattern)  # init
        while curr_problem_start != -1:
            line, col, offset = latexbuddy.tools.absolute_to_linecol(
                tex, curr_problem_start,
            )
            end_command = tex.find("}", curr_problem_start) + 1
            problem_text = tex[curr_problem_start:end_command]
            problems.append(
                Problem(
                    position=(line, col),
                    text=ref_pattern,
                    checker=NativeUseOfRef,
                    category=self.category,
                    file=file.tex_file,
                    severity=self.severity,
                    description=description,
                    context=("", problem_text[5:]),
                    key=self.display_name + "_" + problem_text[5:-1],
                    length=len(ref_pattern),
                ),
            )
            # find next problem for next iteration
            curr_problem_start = tex.find(ref_pattern, curr_problem_start + 1)

        return problems
