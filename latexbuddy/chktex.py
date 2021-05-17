"""This module defines the connection between LaTeXBuddy and ChkTeX."""
from typing import List

import latexbuddy.error_class as error_class
import latexbuddy.tools as tools


# TODO: rewrite this using the Abstract Module API


filename = ""
DELIMITER = ":"
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
    format_str = (
        DELIMITER.join(["%f", "%l", "%c", "%d", "%n", "%s", "%m", "%k"]) + "\n\n"
    )

    command_output = tools.execute("chktex", "-f", f"'{format_str}'", "-q", filename)
    print(command_output)
    out = command_output.split("\n")
    save_output(out, buddy)


def save_output(out: List[str], buddy):
    """Saves the output of ChkTeX as LaTeXBuddy Error objects inside the LaTeXBuddy
    instance.

    :param out: line-split output of the chktex command
    :param buddy: the LaTeXBuddy instance
    """
    for error in out:
        s_arr = error.split(DELIMITER)
        path = s_arr[0]
        if len(s_arr) < 5:
            continue
        warning = True if s_arr[7] == "Warning" else False
        line = int(s_arr[1])
        offset = int(s_arr[2])
        length = int(s_arr[3])
        start = (line, offset)
        suggestions = [s_arr[6]] if len(s_arr[6]) > 0 else []
        id = s_arr[4]
        text = s_arr[5]
        compare_id = "chktex_" + s_arr[1] + "_" + s_arr[5]
        tool_name = "chktex"
        error_type = "latex"
        error_class.Error(
            buddy,
            path,
            tool_name,
            error_type,
            id,
            text,
            start,
            length,
            suggestions,
            warning,
            compare_id,
        )
