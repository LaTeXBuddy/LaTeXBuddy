import hashlib
import os

from pathlib import Path
from typing import List

from unidecode import unidecode

import latexbuddy.tools as tools
from latexbuddy.config_loader import ConfigLoader

from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


class DictionModule(Module):
    def __init__(self):
        self.language = None
        self.tool_name = "diction"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:

        # TODO: make this dynamic/configurable using
        #  config.get_config_option_or_default(
        #       "buddy", "language", "<default language>"
        #  )
        self.language = "de"

        # replace umlauts so error position is correct
        lines = Path(file.plain_file).read_text()
        original_lines = lines.splitlines(keepends=True)

        # print(original_lines)
        lines = unidecode(lines)

        # write cleaned text to tempfile
        cleaned_file = Path(file.plain_file).with_suffix(".cleaned")
        cleaned_file.write_text(lines)

        # execute diction and collect output
        errors = tools.execute(
            f"diction --suggest --language {self.language} {str(cleaned_file)}"
        )

        # remove unnecessary information and split lines
        errors = errors.split("\n")
        errors.pop()
        errors.pop()

        # remove empty lines
        cleaned_errors = []
        for error in errors:
            if len(error) > 0:  # remove empty lines
                cleaned_errors.append(error.strip())

        # remove temp file
        os.remove(cleaned_file)

        # return list of Problems
        return self.format_errors(cleaned_errors, original_lines, file.plain_file, file)

    def format_errors(
        self, out: List[str], original: List[str], file, texfile
    ) -> List[Problem]:
        """Parses diction errors and returns list of Problems.

        :param original: lines of file to check as list
        :param out: line splitted output of the diction command with empty lines removed
        :param file: the file path
        """
        problems = []
        for error in out:

            o_line = ""

            splitted_error = error.split(" ")
            double_world = False

            for i in range(0, len(splitted_error)):
                if splitted_error[i] == "->":
                    if i == len(splitted_error) - 2:
                        break
                    if splitted_error[i + 1] == "Double":
                        double_world = True
                    else:
                        break

            if double_world:

                src, lines, chars, sugg = error.split(":", maxsplit=3)
                splitted_lines = lines.split("-")
                splitted_chars = chars.split("-")
                splitted_lines_int = [int(a) for a in splitted_lines]
                splitted_chars_int = [int(a) for a in splitted_chars]
                start_line, end_line = splitted_lines_int[0], splitted_lines_int[1]
                start_char, end_char = splitted_chars_int[0] - 1, splitted_chars_int[1]
                if start_line == end_line:
                    o_line = original[start_line - 1][start_char:end_char]
                else:
                    for x in range(start_line, end_line + 1):
                        if x == end_line:
                            o_line = o_line + original[x - 1][:end_char]
                        elif x == start_line:
                            o_line = o_line + original[x - 1][start_char:]
                        else:
                            o_line = o_line + original[x - 1]
                location = (start_line, start_char)

            else:
                src, location, sugg = error.split(":", maxsplit=2)
                start_line = int(location.split(".")[0])
                start_char = int(location.split(".")[1].split("-")[0])
                end_line = int(location.split("-")[1].split(".")[0])
                end_char = int(location.split("-")[1].split(".")[1])
                if start_line == end_line:
                    o_line = original[start_line - 1][start_char - 1 : end_char]
                else:
                    for x in range(start_line, end_line + 1):
                        if x == end_line:
                            o_line = o_line + original[x - 1][:end_char]
                        elif x == start_line:
                            o_line = o_line + original[x - 1][start_char:]
                        else:
                            o_line = o_line + original[x - 1]
                location = texfile.get_position_in_tex_from_linecol(
                    start_line, start_char
                )

            problems.append(
                Problem(
                    position=location,
                    text=o_line,
                    checker="diction",
                    cid="0",
                    file=file,
                    severity=ProblemSeverity.INFO,
                    category="wording/ phrasing",
                    suggestions=[sugg],
                    key="diction_" + str(hashlib.md5(o_line.encode())),
                )
            )

        return problems
