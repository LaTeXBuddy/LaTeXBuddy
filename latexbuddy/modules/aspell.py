"""This module defines the connection between LaTeXBuddy and GNU Aspell."""
from __future__ import annotations

import logging
from typing import AnyStr

import latexbuddy.tools as tools
from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from latexbuddy.texfile import TexFile

LOG = logging.getLogger(__name__)


class Aspell(Module):
    def __init__(self):
        self.language = None

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        """Runs the Aspell checks on a file and returns the results as a list.

        Requires Aspell to be set up.

        :param config: the configuration options of the calling
                       LaTeXBuddy instance
        :param file: LaTeX file to be checked (with built-in detex
                     option)
        """

        tools.find_executable("aspell", "GNU Aspell", LOG)

        supported_languages = self.find_languages()

        self.language = config.get_config_option_or_default(
            LatexBuddy,
            "language",
            "en",
            verify_type=AnyStr,
            verify_choices=supported_languages,
        )

        language_country = config.get_config_option_or_default(
            LatexBuddy,
            "language_country",
            None,
            verify_type=AnyStr,
        )

        if (
            language_country is not None
            and self.language + "-" + language_country in supported_languages
        ):
            self.language = self.language + "-" + language_country

        error_list = []
        counter = 1  # counts the lines

        # execute aspell on given file and collect output
        lines = file.plain.splitlines(keepends=False)
        for line in lines:  # check every line
            if len(line) > 0:
                escaped_line = line.replace("'", "\\'")
                output = tools.execute(
                    f"echo '{escaped_line}' | aspell -a -l {self.language}",
                )
                # the first line specifies aspell version
                out = output.splitlines()[1:]
                if len(out) > 0:  # only if the list inst empty
                    out.pop()  # remove last element
                error_list.extend(self.format_errors(out, counter, file))

            # if there is an empty line, just increase the counter
            counter += 1

        return error_list

    @staticmethod
    def find_languages() -> list[str]:
        """Returns all languages supported by the current aspell installation.
        Omits specific language variations like 'en- variant_0'.

        :return: list of supported languages in str format
        """
        return [
            lang
            for lang in tools.execute("aspell", "dump dicts").splitlines()
            if "-" not in lang
        ]

    def format_errors(
        self,
        out: list[str],
        line_number: int,
        file: TexFile,
    ) -> list[Problem]:
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
            if error[0] not in ("&", "#"):
                continue

            tmp = error[1:].strip().split(": ", 1)
            if len(tmp) == 1:
                tmp.append("")
            meta_str, suggestions_str = tmp

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
                line_number,
                char_location,
            )
            key = "spelling" + key_delimiter + text

            problems.append(
                Problem(
                    position=location,
                    text=text,
                    checker=Aspell,
                    file=file.tex_file,
                    severity=severity,
                    p_type=p_type,
                    category="spelling",
                    suggestions=suggestions,
                    key=key,
                ),
            )
        return problems
