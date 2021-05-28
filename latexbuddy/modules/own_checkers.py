import re
from typing import List

import latexbuddy.tools as tools

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


class UnreferencedFiguresModule(Module):
    def __init__(self):
        self.tool_name = "refcheck"
        self.cid = "0"
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
        figures = re.findall(pattern, tex)
        len_label = len("label{")
        labels = {}
        for figure in figures:
            match = re.search(re.escape(figure), tex)
            absolute_position = match.span()[0]
            length = match.span()[1] - match.span()[0]
            split = figure.split("\\")
            for word in split:
                if (
                    re.search(re.escape("label{") + ".*" + re.escape("}"), word)
                    is not None
                ):
                    label = word[len_label : len(word) - 2]
                    labels[label] = (absolute_position, length)
        for label in labels.keys():
            pos_len = labels[label]
            position = pos_len[0]
            length = pos_len[1]
            line, col, offset = tools.absolute_to_linecol(file.tex, position)
            if re.search(re.escape("\\ref{") + label + re.escape("}"), tex) is None:
                problems.append(
                    Problem(
                        position=(line, col),
                        text=label,
                        checker=self.tool_name,
                        category=self.category,
                        cid=self.cid,
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
        text = file.tex
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
                    cid="num",
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
                        cid="unit",
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
                    cid="0",
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
        pattern = "(http|ftp|https)(:\/\/)([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
        urls = re.findall(pattern, tex)
        for url_list in urls:
            url = ""
            for u in url_list:
                url += u
            match = re.search(re.escape(url), tex)
            start, end = match.span()
            length = end - start
            command_len = len("\\url{")
            if tex[start - command_len : start] == "\\url{":
                continue
            line, col, offset = tools.absolute_to_linecol(tex, start)
            problems.append(
                Problem(
                    position=(line, col),
                    text=url,
                    checker=self.tool_name,
                    category=self.category,
                    cid="0",
                    file=file.tex_file,
                    severity=self.severity,
                    description=f"For URLs use \\url.",
                    key=self.tool_name + "_" + url,
                    length=length,
                )
            )
        return problems
