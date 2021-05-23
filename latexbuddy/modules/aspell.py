"""This module defines the connection between LaTeXBuddy and GNU Aspell."""

import shlex

from typing import List

import latexbuddy.buddy as ltb
import latexbuddy.tools as tools

from latexbuddy.abs_module import Module
from pathlib import Path
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


class AspellModule(Module):
    def __init__(self):
        self._LANGUAGE_MAP = {"de": "de-DE", "en": "en"}
        self.language = "de"
        self.tool_name = "aspell"

    def run_checks(self, buddy: ltb.LatexBuddy, file: TexFile) -> List[Problem]:
        """Runs the Aspell checks on a file and returns the results as a list.

        Requires Aspell to be set up.

        :param buddy: the LaTeXBuddy instance
        :param file: the file to run checks on
        """

        try:
            tools.find_executable("aspell")
        except FileNotFoundError:
            print("Could not find a valid aspell installation on your system.")
            print("Please make sure you installed aspell correctly.")

            print("For more information check the LaTeXBuddy manual.")

            raise FileNotFoundError("Unable to find aspell installation!")

        try:
            self.language = self._LANGUAGE_MAP[buddy.lang]
        except KeyError:
            self.language = None
        language_quote = shlex.quote(self.language)
        languages = tools.execute("aspell", "dump dicts")
        AspellModule.check_language(language_quote, languages)

        error_list = []
        counter = 1  # counts the lines

        # execute aspell on given file and collect output
        lines = Path(file.plain_file).read_text().splitlines(keepends=False)
        for line in lines:  # check every line
            if len(line) > 0:
                output = tools.execute(f"echo {line} | aspell -a")
                out = output.splitlines()[1:]  # the first line specifies aspell version
                if len(out) > 0:  # only if the list inst empty
                    out.pop()  # remove last element
                error_list.extend(self.format_errors(out, counter, file))
                counter += 1
            else:
                counter += 1  # if there is an empty line, just increase the counter

        return error_list

    @staticmethod
    def check_language(language: str, langs: str):
        """Checks if a language is in a list of languages.

        The list of languages is actually a string; e.g., the output of a terminal
        command.

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

    def format_errors(self, out: List[str], line_number: int, file: TexFile) -> List[
        Problem]:
        """Parses Aspell errors and returns list of Problems.

        :param line_number: the line_number for the location
        :param out: line-split output of the aspell command
        :param file: the file path
        """
        cid = "0"  # aspell got not error-ids
        severity = ProblemSeverity.ERROR
        key_delimiter = "_"
        problems = []

        for error in out:
            if error[0] in ("&", "#"):
                tmp = error[1:].strip().split(": ", 1)
                meta_str, suggestions_str = tmp if len(tmp) > 1 else (tmp[0], "")

                meta = meta_str.split(" ")
                text = meta[0]

                suggestions = []
                # & if there are suggestions
                if error[0] == "&":
                    suggestions = suggestions_str.split(", ")
                # just take the first 5 suggestions
                if len(suggestions) > 5:
                    suggestions = suggestions[0:5]

                # calculate the char location
                tmp_split = tmp[0].split(" ")
                if error[0] in "&":  # if there are sugestions
                    char_location = int(tmp_split[2])
                else:  # if there are no suggestions
                    char_location = int(tmp_split[1])

                location = (line_number, char_location)  # meta[1] is the char position
                key = self.tool_name + key_delimiter + text

                problems.append(
                    Problem(
                        position=location,
                        text=text,
                        checker=self.tool_name,
                        cid=cid,
                        file=file.tex_file,
                        severity=severity,
                        category="spelling",
                        suggestions=suggestions,
                        key=key,
                    )
                )
        return problems
