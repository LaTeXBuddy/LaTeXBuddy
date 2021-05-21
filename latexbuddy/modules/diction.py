from pathlib import Path
from typing import List

import latexbuddy.buddy as ltb
import latexbuddy.tools as tools

from latexbuddy.abs_module import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


class DictionModule(Module):
    def __init__(self):
        self.language = None
        self.tool_name = "diction"

    def run_checks(self, buddy: ltb.LatexBuddy, file: TexFile) -> List[Problem]:
        self.language = buddy.lang
        errors = tools.execute(
            f"diction --suggest --language {self.language} {str(file)}"
        )

        errors = errors[: len(errors) - 35]  # remove unnecessary information
        errors = errors.split("\n")

        cleaned_errors = []
        for error in errors:
            if len(error) > 0:  # remove empty lines
                cleaned_errors.append(error.strip())

        return self.format_errors(cleaned_errors, file)

    def format_errors(self, out: List[str], file) -> List[Problem]:
        """Parses diction errors and returns list of Problems.

        :param out: line stripped output of the diction command with empty lines removed
        :param file: the file path
        """
        problems = []
        for error in out:
            print(error)
            src, location, sugg = error.split(":", maxsplit=2)
            print(f"src={src}, loc={location}, sugg={sugg}")

            line = location.split(".")[0]
            print("line=" + line)
            num = location.split(".")[1].split("-")[0]
            print("num=" + num)

            problems.append(
                Problem(
                    position=(line, num),
                    text=sugg,
                    checker="diction",
                    cid="0",
                    file=file.tex_file,
                    severity=ProblemSeverity.INFO,
                    category="wording/ phrasing",
                    suggestions=sugg,
                    key="diction_" + "wip",
                )
            )

            return problems
