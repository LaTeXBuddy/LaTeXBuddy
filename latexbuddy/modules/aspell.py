"""This module defines the connection between LaTeXBuddy and GNU Aspell."""

import shlex

from typing import List

import latexbuddy.buddy as ltb
import latexbuddy.tools as tools

from latexbuddy.abs_module import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


class AspellModule(Module):
    def __init__(self):
        self._LANGUAGE_MAP = {"de": "de-DE", "en": "en"}
        self.language = None
        self.tool_name = "aspell"

    def run_checks(self, buddy: ltb.LatexBuddy, file: TexFile) -> List[Problem]:
        """Runs the Aspell checks on a file and returns the results as a list.

        Requires Aspell to be set up.

        :param buddy: the LaTeXBuddy instance
        :param file: the file to run checks on
        """
        try:
            self.language = self._LANGUAGE_MAP[buddy.lang]
        except KeyError:
            self.language = None
        language_quote = shlex.quote(self.language)
        languages = tools.execute("aspell", "dump dicts")
        AspellModule.check_language(language_quote, languages)
        # execute aspell on given file and collect output
        error_list = tools.execute(
            f"cat {str(file)} | aspell -a --lang={self.language}"
        )

        # format aspell output
        out = error_list.splitlines()[1:]  # the first line specifies aspell version

        # cleanup error list
        return self.format_errors(out, file)

    @staticmethod
    def check_language(language: str, langs: str):
        """Checks if a language is in a list of languages.

        The list of languages is actually a string; e.g., the output of a terminal command.

        :param language: language to search for
        :param langs: language list to search in
        :raises Exception: if the language is not on the list
        """
        # error if language dict not installed
        if language not in langs:
            print(f'Dictionary for language "{language}" not found')
            print("Install dictionary (e.g. via package manager)")
            print(
                "check available dictionaries "
                "at https://ftp.gnu.org/gnu/aspell/dict/0index.html"
            )
            raise Exception("Aspell: Language not found on system.")

    def format_errors(self, out: List[str], file: TexFile) -> List[Problem]:
        """Parses Aspell errors and returns list of Problems.

        :param out: line-split output of the aspell command
        :param file: the file path
        """
        cid = "0"  # aspell got not error-ids
        severity = ProblemSeverity.ERROR
        key_delimiter = "_"
        line_number = 1
        problems = []
        # line_offsets = tools.calculate_line_offsets(file)

        for error in out:
            if error.strip() == "":
                # this is a line separator
                line_number += 1
                continue

            if error[0] in ("&", "#"):
                tmp = error[1:].strip().split(": ", 1)
                meta_str, suggestions_str = tmp if len(tmp) > 1 else (tmp[0], "")

                # & original count offset
                # # original
                meta = meta_str.split(" ")

                text = meta[0]
                suggestions = []

                if error[0] == "&":  # there are suggestions
                    # location = int(meta[2])  # meta[1] is suggestion count
                    suggestions = suggestions_str.split(", ")
                # else:  # there are no suggestions
                # location = int(meta[1])

                # location = line_offsets[line_number + 1] + location  # absolute pos in detex

                # location = tools.find_char_position(buddy.file_to_check, Path(file),
                #                                    buddy.charmap,
                #                                    location)  # absolute pos in tex
                location = (0, 0)  # aspell's locations are funky
                key = self.tool_name + key_delimiter + text

                problems.append(
                    Problem(
                        location,
                        text,
                        self.tool_name,
                        cid,
                        file.tex_file,
                        severity,
                        None,
                        None,
                        None,
                        suggestions,
                        key,
                    )
                )
        return problems
