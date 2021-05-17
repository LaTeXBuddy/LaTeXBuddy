"""This module defines the connection between LaTeXBuddy and GNU Aspell."""

import shlex

from pathlib import Path, PurePath
from typing import List

import latexbuddy.error_class as error_class
import latexbuddy.tools as tools


_LANGUAGES = {"de": "de-DE", "en": "en"}


# TODO: rewrite this using the Abstract Module API
def run(buddy, file: Path):
    """Runs the aspell checks on a file and saves the results in a LaTeXBuddy
    instance.

    Requires aspell to be separately installed

    :param buddy: the LaTeXBuddy instance
    :param file: the file to run checks on
    """
    language = _LANGUAGES[buddy.lang]
    language = shlex.quote(language)
    langs = tools.execute("aspell", "dump dicts")
    check_language(language, langs)
    # execute aspell on given file and collect output
    error_list = tools.execute(f"cat {str(file)} | aspell -a --lang={language}")

    # format aspell output
    out = error_list.splitlines()[1:]  # the first line specifies aspell version

    # cleanup error list
    format_errors(out, buddy, file)


# TODO: possibly inline unnecessary method
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

        # TODO: remove APT reference; it's not on every distro
        print("Install dictionary via sudo apt install")
        print(
            "check available dictionaries "
            "at https://ftp.gnu.org/gnu/aspell/dict/0index.html"
        )
        raise Exception("Spell check Failed")  # TODO: write a better Exception message


# TODO: use pathlib.Path
def format_errors(out: List[str], buddy, file: Path):
    """Parses Aspell errors and converts them to LaTeXBuddy Error objects.

    :param out: line-split output of the aspell command
    :param buddy: the LaTeXBuddy instance
    :param file: the file path
    """
    line_number = 1
    line_offsets = tools.calculate_line_offsets(file)

    for error in out:
        if error.strip() == "":
            # this is a line separator
            line_number += 1
            continue

        if error[0] in ("&", "#"):

            tmp = error[1:].strip().split(": ", 1)
            meta_str, suggestions_str = tmp if len(tmp) > 1 else (tmp[0], [])

            # & original count offset
            # # original
            meta = meta_str.split(" ")

            text = meta[0]
            suggestions = []

            if error[0] == "&":  # there are suggestions
                location = int(meta[2])  # meta[1] is suggestion count
                suggestions = suggestions_str.split(", ")
            else:  # there are no suggestions
                location = int(meta[1])

            # location = line_offsets[line_number + 1] + location  # absolute pos in detex

            # location = tools.find_char_position(buddy.file_to_check, Path(file),
            #                                    buddy.charmap,
            #                                    location)  # absolute pos in tex
            location = None

            error_class.Error(
                buddy,
                PurePath(file).stem,
                "aspell",
                "spelling",
                "0",
                text,
                location,
                len(text),
                suggestions,
                False,
                "spelling_" + text,
            )
