"""This module defines the connection between LaTeXBuddy and ChkTeX."""
from typing import List

import latexbuddy.error_class as error_class
import latexbuddy.tools as tools


# TODO: rewrite this using the Abstract Module API


filename = ""
line_lengths = []  # TODO: please don't use global variables. Like, anywhere.


# TODO: use pathlib.Path instead of strings
def run(buddy, file: str):
    """Runs the chktex checks on a file and saves the results in a LaTeXBuddy
    instance.

    Requires chktex to be separately installed

    :param buddy: the LaTeXBuddy instance
    :param file: the file to run checks on
    """
    global line_lengths
    global filename
    filename = file
    line_lengths = tools.calculate_line_lengths(filename)
    out = tools.execute(
        "chktex", '-f "%f:%l:%c:%d:%n:%s:%m:%k\n"', "-q", filename
    ).split("\n")
    save_output(out, buddy)


def save_output(out: List[str], buddy):
    """Saves the output of ChkTeX as LaTeXBuddy Error objects inside the LaTeXBuddy
    instance.

    :param out: line-split output of the chktex command
    :param buddy: the LaTeXBuddy instance
    """
    for error in out:
        s_arr = error.split(":")
        if len(s_arr) < 5:
            continue
        warning = True if s_arr[7] == "Warning" else False
        line = int(s_arr[2])
        offset = int(s_arr[3])
        length = int(s_arr[4])
        start = tools.start_char(line, offset, line_lengths)
        suggestions = [s_arr[6]] if len(s_arr[6]) > 0 else []
        error_class.Error(
            buddy,
            s_arr[0],
            "chktex",
            "latex",
            s_arr[1],
            s_arr[5],
            start,
            length,
            suggestions,
            warning,
            "chktex_" + s_arr[1] + "_" + s_arr[5],
        )
