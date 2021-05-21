import os
from pathlib import Path
from typing import List
from unidecode import unidecode

from latexbuddy.abs_module import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile

import latexbuddy.buddy as ltb
import latexbuddy.tools as tools


class DictionModule(Module):
    def __init__(self):
        self.language = None
        self.tool_name = "diction"

    def run_checks(self, buddy: ltb.LatexBuddy, file: TexFile) -> List[Problem]:
        self.language = "de"

        #replace umlauts so error position is correct
        lines = Path(file.plain_file).read_text()
        lines = unidecode(lines)

        #write cleaned text to tempfile
        cleaned_file = Path(file.plain_file).with_suffix(".cleaned")
        cleaned_file.write_text(lines)

        #execute diction and collect output
        errors = tools.execute(
            f"diction --suggest --language {self.language} {str(cleaned_file)}"
        )

        # remove unnecessary information and split lines
        errors = errors[: len(errors) - 35]
        errors = errors.split("\n")

        #remove empty lines
        cleaned_errors = []
        for error in errors:
            if len(error) > 0:  # remove empty lines
                cleaned_errors.append(error.strip())
                print(error)

        # remove temp file
        os.remove(cleaned_file)

        return self.format_errors(cleaned_errors, file.plain_file)

    def format_errors(self, out: List[str], file) -> List[Problem]:
        """Parses diction errors and returns list of Problems.

        :param out: line stripped output of the diction command with empty lines removed
        :param file: the file path
        """
        problems = []
        for error in out:

            if "Double word" in error:
                src, lines, chars, sugg = error.split(":", maxsplit=3)
                splitted_lines = lines.split("-")
                splitted_chars = chars.split("-")
                splitted_lines_int = [int(a) for a in splitted_lines]
                splitted_chars_int = [int(a) for a in splitted_chars]
                start_line, end_line = splitted_lines_int[0], splitted_lines_int[1]
                start_char, end_char = splitted_chars_int[0], splitted_chars_int[1]
                print(f"Double word error: src={src}, start_line={start_line},end_line={end_line},start_char={start_char}, end_char={end_char}, sugg={sugg}")
                location = (start_line, start_char)
            else:
                src, location, sugg = error.split(":", maxsplit=2)
                print(f"Wording error: src={src}, loc={location}, sugg={sugg}")
                line = int(location.split(".")[0])
                num = int(location.split(".")[1].split("-")[0])
                location = (line, num)

            problems.append(
                Problem(
                    position=location,
                    text=sugg,
                    checker="diction",
                    cid="0",
                    file=file,
                    severity=ProblemSeverity.INFO,
                    category="wording/ phrasing",
                    suggestions=[sugg],
                    key="diction_" + "wip",
                )
            )

        return problems
