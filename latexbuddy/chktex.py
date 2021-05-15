import shlex
import subprocess

import latexbuddy.error_class as error_class
import latexbuddy.tools as tools


filename = ""
line_lengths = []


def run(buddy, file):
    global line_lengths
    global filename
    filename = file
    line_lengths = tools.calculate_line_lengths(filename)
    out = tools.execute(
        "chktex", '-f "%f:%l:%c:%d:%n:%s:%m:%k\n"', "-q", filename
    ).split("\n")
    save_output(out, buddy, file)


def save_output(out, buddy, file):
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
