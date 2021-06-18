import os
import re

from typing import List

import latexbuddy.tools as tools

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


class UnreferencedFiguresModule(Module):
    def __init__(self):
        self.tool_name = "unrefed_figure_check"
        self.p_type = "0"
        self.severity = ProblemSeverity.INFO
        self.category = "latex"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        """Finds unreferenced figures.
        :param: config: configurations of the buddy instance
        :param: file: the file to check
        :return: a list of found problems
        """
        tex = file.tex
        problems = []
        pattern = r"\\begin{figure}[\w\W]*?\\end{figure}"
        figures = re.finditer(pattern, tex)
        len_label = len("label{")
        labels = {}

        for figure_match in figures:
            start, end = figure_match.span()
            length = end - start
            split = figure_match.group(0).split("\\")
            for word in split:
                label_match = re.search(re.escape("label{") + "(.*)" + re.escape("}"), word)
                if label_match is not None:
                    label = label_match.group(1)
                    labels[(start, length)] = label

        for (position, length), label in labels.items():
            line, col, offset = tools.absolute_to_linecol(file.tex, position)
            if re.search(re.escape("\\ref{") + label + re.escape("}"), tex) is None:
                problems.append(
                    Problem(
                        position=(line, col),
                        text=label,
                        checker=self.tool_name,
                        category=self.category,
                        p_type=self.p_type,
                        file=file.tex_file,
                        severity=self.severity,
                        description=f"Figure {label} not referenced.",
                        key=self.tool_name + "_" + label,
                        length=length,
                        context=("\\label{", "}"),
                    )
                )

        return problems


class SiUnitxModule(Module):
    def __init__(self):
        self.tool_name = "siunitx"
        self.category = "latex"
        self.severity = ProblemSeverity.INFO

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        """Finds units and long numbers used without siunitx package.
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

    def find_long_numbers(self, file: TexFile) -> List[Problem]:
        """Finds long numbers used without siunitx package.
        :param: file: the file to check
        :return: a list of found problems
        """
        problems = []
        text = file.tex
        all_numbers = re.findall("[0-9]+", text)
        threshold = 3

        def filter_big_numbers(n):
            return True if len(n) > threshold else False

        numbers = list(filter(filter_big_numbers, all_numbers))

        for number in numbers:
            match = re.search(re.escape(str(number)), text)
            start, end = match.span()
            length = end - start
            line, col, offset = tools.absolute_to_linecol(text, start)
            problems.append(
                Problem(
                    position=(line, col),
                    text=str(number),
                    checker=self.tool_name,
                    category=self.category,
                    p_type="num",
                    file=file.tex_file,
                    severity=self.severity,
                    description=f"For number {number} \\num from siunitx may be used.",
                    key=self.tool_name + "_" + str(number),
                    length=length,
                )
            )
        return problems

    def find_units(self, file: TexFile) -> List[Problem]:
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
            used_unit = re.findall(pattern, text)
            used_units.append(used_unit)

        for used_unit in used_units:
            for unit in used_unit:
                match = re.search(re.escape(unit), text)
                start, end = match.span()
                length = end - start
                line, col, offset = tools.absolute_to_linecol(text, start)
                problems.append(
                    Problem(
                        position=(line, col),
                        text=unit,
                        checker=self.tool_name,
                        category=self.category,
                        p_type="unit",
                        file=file.tex_file,
                        severity=self.severity,
                        description=f"For unit {unit} siunitx may be used.",
                        key=self.tool_name + "_" + unit,
                        length=length,
                    )
                )

        return problems


class EmptySectionsModule(Module):
    def __init__(self):
        self.tool_name = "emptysection"
        self.category = "latex"
        self.severity = ProblemSeverity.INFO

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        tex = file.tex
        problems = []
        pattern = r"\\section{.*}\s+\\subsection"
        empty_sections = re.findall(pattern, tex)
        for section in empty_sections:
            match = re.search(re.escape(section), tex)
            start, end = match.span()
            length = end - start
            line, col, offset = tools.absolute_to_linecol(tex, start)
            sec_len = len("\\section{")
            rest_pattern = r"}\s+\\subsection"
            rest_match = re.findall(rest_pattern, section)
            rest_len = len(rest_match[0])
            text = section[sec_len : len(section) - rest_len]
            problems.append(
                Problem(
                    position=(line, col),
                    text=text,
                    checker=self.tool_name,
                    category=self.category,
                    p_type="0",
                    file=file.tex_file,
                    severity=self.severity,
                    description=f"Sections may not be empty.",
                    key=self.tool_name + "_" + text,
                    length=length,
                    context=("\\section{", "}"),
                )
            )
        return problems


class URLModule(Module):
    def __init__(self):
        self.tool_name = "urlcheck"
        self.category = "latex"
        self.severity = ProblemSeverity.INFO

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        tex = file.tex
        problems = []
        # https://stackoverflow.com/questions/6038061/regular-expression-to-find-urls-within-a-string
        pattern = r"(http|ftp|https)(:\/\/)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
        urls = re.finditer(pattern, tex)

        for url_match in urls:

            start, end = url_match.span()
            length = end - start
            command_len = len("\\url{")
            if tex[start - command_len : start] == "\\url{":
                continue
            line, col, offset = tools.absolute_to_linecol(tex, start)
            problems.append(
                Problem(
                    position=(line, col),
                    text=url_match.group(0),
                    checker=self.tool_name,
                    category=self.category,
                    p_type="0",
                    file=file.tex_file,
                    severity=self.severity,
                    description=f"For URLs use \\url.",
                    key=self.tool_name + "_" + url_match.group(0),
                    length=length,
                )
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
        "tiff",
        "tif",
        ".psd",
        ".dip",
        ".heif",
        ".heic",
        ".jp2",
    ]

    def __init__(self):
        self.tool_name = "resolution_check"
        self.p_type = "0"
        self.severity = ProblemSeverity.INFO
        self.category = "latex"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        """Finds potential low resolution figures.
        :param: config: configurations of the buddy instance
        :param: file: the file to check
        :return: a list of found problems
        """
        search_root = os.path.dirname(file.tex_file)
        problems = []
        figures = []

        for root, dirs, files in os.walk(search_root):
            root_name = os.path.basename(root)
            for current_file in files:
                name, ending = os.path.splitext(current_file)
                if str.lower(ending) in self.file_endings or (
                    str.lower(root_name) == "figures" and str.lower(ending) == ".pdf"
                ):
                    figures.append(current_file)
                    problems.append(
                        Problem(
                            position=(1, 1),
                            text=name,
                            checker=self.tool_name,
                            category=self.category,
                            p_type="0",
                            file=file.tex_file,
                            severity=self.severity,
                            description=f"Figure might have low resolution due to file format {ending}",
                            key=self.tool_name + "_" + current_file,
                            length=1,
                        )
                    )

        return problems


class NativeUseOfRef(Module):
    def __init__(self):
        self.tool_name = "native_ref_use_check"
        self.severity = ProblemSeverity.INFO
        self.category = "latex"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        description = "Instead of \\ref{} use a more precise command e.g. \\cref{}"
        tex = file.tex
        problems = []
        ref_pattern = "\\ref{"

        curr_problem_start = tex.find(ref_pattern)  # init
        while curr_problem_start != -1:
            line, col, offset = tools.absolute_to_linecol(tex, curr_problem_start)
            end_command = tex.find("}", curr_problem_start) + 1
            problem_text = tex[curr_problem_start:end_command]
            problems.append(
                Problem(
                    position=(line, col),
                    text=ref_pattern,
                    checker=self.tool_name,
                    category=self.category,
                    file=file.tex_file,
                    severity=self.severity,
                    description=description,
                    context=("", problem_text[5:]),
                    key=self.tool_name + "_" + problem_text[5:-1],
                    length=len(ref_pattern),
                )
            )
            # find next problem for next iteration
            curr_problem_start = tex.find(ref_pattern, curr_problem_start + 1)

        return problems
