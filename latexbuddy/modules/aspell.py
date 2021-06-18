"""This module defines the connection between LaTeXBuddy and GNU Aspell."""
import shlex

from typing import List

import latexbuddy.tools as tools

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.exceptions import LanguageNotSupportedError
from latexbuddy.messages import not_found
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


class AspellModule(Module):
    def __init__(self):
        self._LANGUAGE_MAP = {"de": "de-DE", "en": "en"}
        self.language = "en"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        """Runs the Aspell checks on a file and returns the results as a list.

        Requires Aspell to be set up.

        :param config: the configuration options of the calling LaTeXBuddy instance
        :param file: LaTeX file to be checked (with built-in detex option)
        """

        tools.find_executable("aspell", "GNU Aspell", self.logger)

        try:

            self.language = self._LANGUAGE_MAP[
                config.get_config_option_or_default(LatexBuddy, "language", None)
            ]

        except KeyError:
            self.language = None

        language_quote = shlex.quote(self.language)
        languages = tools.execute("aspell", "dump dicts")
        self.check_language(language_quote, languages)

        error_list = []
        counter = 1  # counts the lines

        # execute aspell on given file and collect output
        lines = file.plain.splitlines(keepends=False)
        for line in lines:  # check every line
            if len(line) > 0:
                escaped_line = line.replace("'", "\\'")
                output = tools.execute(
                    f"echo '{escaped_line}' | aspell -a -l {language_quote}"
                )
                out = output.splitlines()[1:]  # the first line specifies aspell version
                if len(out) > 0:  # only if the list inst empty
                    out.pop()  # remove last element
                error_list.extend(self.format_errors(out, counter, file))

            counter += 1  # if there is an empty line, just increase the counter

        return error_list

    def check_language(self, language: str, langs: str):
        """Checks if a language is in a list of languages.

        The list of languages is actually a string; e.g., the output of a terminal
        command.

        :param language: language to search for
        :param langs: language list to search in
        :raises LanguageNotSupportedError: if the language is not on the list
        """
        # error if language dict not installed
        if language not in langs:
            self.logger.error(
                not_found(f"Language for {language}", "the dictionary")
                + "\nYou can check available dictionaries at "
                + "https://ftp.gnu.org/gnu/aspell/dict/0index.html"
            )

            raise LanguageNotSupportedError(
                f"Aspell: Language '{language}' not found on system."
            )

    def format_errors(
        self, out: List[str], line_number: int, file: TexFile
    ) -> List[Problem]:
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
                if error[0] in "&":  # if there are suggestions
                    char_location = int(tmp_split[2]) + 1
                else:  # if there are no suggestions
                    char_location = int(tmp_split[1]) + 1

                location = file.get_position_in_tex_from_linecol(
                    line_number, char_location
                )
                key = "spelling" + key_delimiter + text

                problems.append(
                    Problem(
                        position=location,
                        text=text,
                        checker=self,
                        file=file.tex_file,
                        severity=severity,
                        p_type=p_type,
                        category="spelling",
                        suggestions=suggestions,
                        key=key,
                    )
                )
        return problems
