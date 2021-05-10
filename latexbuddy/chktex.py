import shlex
import subprocess

import latexbuddy.error_class as error_class
import latexbuddy.tools as tools


filename = ""
line_lengths = []


def run(buddy, file):
    global filename
    filename = file
    calculate_line_lengths()
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
        start = start_char(line, offset)
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
        )


"""
Calculates the lengths of each line
To later convert the line, offset to starting char
"""


def calculate_line_lengths():
    file = open(filename, "r", encoding="utf-8", errors="ignore")
    lines = file.readlines()
    file.close()
    for line in lines:
        line_lengths.append(len(line))


"""
Calculates the starting character based on line and offset
"""


def start_char(line, offset):
    start = 0
    for i in range(len(line_lengths)):
        if i < line:
            start += line_lengths[i]
    return start + offset
