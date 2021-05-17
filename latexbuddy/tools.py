"""This module contains various utilitary tools."""

import os
import re
import signal
import subprocess
import sys
from io import StringIO

from pathlib import Path, PurePath
from typing import List, Tuple, Optional

from yalafi.tex2txt import Options, get_line_starts, tex2txt, translate_numbers


def execute(*cmd: str, encoding: str = "ISO8859-1") -> str:
    """Executes a terminal command with subprocess.

    See usage example in latexbuddy.aspell.

    :param cmd: command name and arguments
    :param encoding: output encoding
    :return: command output
    """
    command = get_command_string(cmd)

    error_list = subprocess.Popen(
        [command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    out, err_out = error_list.communicate()
    return out.decode(encoding)


def execute_background(*cmd: str) -> subprocess.Popen:
    """Executes a terminal command in background.

    :param cmd: command name and arguments
    :return: subprocess instance of the executed command
    """
    command = get_command_string(cmd)

    process = subprocess.Popen(
        [command],
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )
    return process


def kill_background_process(process: subprocess.Popen):
    """Kills previously opened background process.

    For example, it can accept the return value of execute_background() as argument.

    :param process: subprocess instance of the process
    """
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)


def execute_no_errors(*cmd: str, encoding: str = "ISO8859-1") -> str:
    """Executes a terminal command while suppressing errors.

    :param cmd: command name and arguments
    :param encoding: output encoding
    :return: command output
    """
    command = get_command_string(cmd)

    error_list = subprocess.Popen(
        [command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    out, err_out = error_list.communicate()
    return out.decode(encoding)


def get_command_string(cmd: Tuple[str]) -> str:
    """Constructs a command string from a tuple of arguments.

    :param cmd: tuple of command line arguments
    :return: the command string
    """
    command = ""
    for arg in cmd:
        command += str(arg) + " "
    return command.strip()


def find_executable(name: str) -> str:
    """Finds path to an executable.

    This uses 'which', i.e. the executable should at least be in user's $PATH

    :param name: executable name
    :return: path to the executable
    :raises FileNotFoundError: if the executable couldn't be found
    """
    result = execute("which", name)

    if not result or "not found" in result:
        raise FileNotFoundError(f"could not find {name} in system's PATH")
    else:
        return result.splitlines()[0]


def detex(file_to_detex: Path) -> Path:
    """Strips TeX control structures from a file.

    Using OpenDetex, removes TeX code from the file, leaving only the content behind.

    :param file_to_detex: path to the file to be detex'ed
    :return: path to the detex'ed file
    :raises FileNotFoundError: if detex executable couldn't be found
    """
    try:
        find_executable("detex")
    except FileNotFoundError:
        print("Could not find a valid detex installation on your system.")
        print("Please make sure you installed detex correctly, and it is in your ")
        print("System's PATH.")

        print("For more information check the LaTeXBuddy manual.")

        raise FileNotFoundError("Unable to find detex installation!")

    detexed_file = file_to_detex.with_suffix(".detexed")
    execute("detex", str(file_to_detex), " > ", str(detexed_file))
    return detexed_file


def detex_path(file_to_detex: Path) -> Path:
    """Strips TeX control structures from a file.

    Using OpenDetex, removes TeX code from the file, leaving only the content behind.

    :param file_to_detex: path to the file to be detex'ed
    :return: path to the detex'ed file
    :raises FileNotFoundError: if detex executable couldn't be found
    """
    try:
        find_executable("detex")
    except FileNotFoundError:
        print("Could not find a valid detex installation on your system.")
        print("Please make sure you installed detex correctly, and it is in your ")
        print("System's PATH.")

        print("For more information check the LaTeXBuddy manual.")

        raise FileNotFoundError("Unable to find detex installation!")

    detexed_file = Path(file_to_detex).with_suffix(".detexed")
    execute("detex", "-s", str(file_to_detex.absolute()), " > ", str(detexed_file))
    return detexed_file


location_re = re.compile(r'line (\d+), column (\d+)')


def yalafi_detex(file_to_detex: Path) -> Tuple[
    Path,
    List[int],
    List[
        Tuple[
            Optional[Tuple[int, int]],
            str
        ]
    ]
]:
    tex = file_to_detex.read_text()
    opts = Options()

    # parse output of tex2txt to err variable
    my_stderr = StringIO()
    sys.stderr = my_stderr
    plain, charmap = tex2txt(tex, opts)  # TODO: save charmap somewhere
    sys.stderr = sys.__stderr__
    out = my_stderr.getvalue()
    my_stderr.close()

    out_split = out.split("*** LaTeX error: ")
    err = []

    for yalafi_error in out_split[1:]:
        location_str, _, reason = yalafi_error.partition("***")

        location_match = location_re.match(location_str)
        if location_match:
            location = (int(location_match.group(1)), int(location_match.group(2)))
        else:
            location = None

        err.append((location, reason.strip()))

    # write to detexed file
    detexed_file = Path(file_to_detex).with_suffix(".detexed")  # TODO: use tempfile
    detexed_file.write_text(plain)

    return detexed_file, charmap, err


def find_char_position(
    original_file: Path, detexed_file: Path, charmap: List[int], char_pos: int
) -> Optional[Tuple[int, int]]:
    """Calculates line and col position of a character in the original file based on its
    position in detex'ed file.

    :param original_file: path to the original tex file
    :param detexed_file: path to the detex'ed version of that file
    :param charmap: the charmap to resolve the position
    :param char_pos: absolute position of char in detexed file. \n counts as one char. Starts counting with 1
    """
    tex = original_file.read_text()
    plain = detexed_file.read_text()
    line_starts = get_line_starts(plain)  # [0, ...]
    line = 0
    while char_pos >= line_starts[line]:
        line += 1
    start = line_starts[line - 1]
    char = char_pos - start + 1

    # translate_numbers() need 1-basd line and char numbers
    # line_starts has 0-based numbers
    aux = translate_numbers(tex, plain, charmap, line_starts, line, char)

    if aux is None:
        return None
        # raise Exception("File parsing error while converting tex to txt.")

    return aux.lin, aux.col


if __name__ == '__main__':
    orig = Path("../tests/test.tex")
    detexed, charmap = yalafi_detex(orig)
    find_char_position(orig, detexed, charmap, 9)


def start_char(line: int, offset: int, line_lengths: List[int]) -> int:
    """Calculates the absolute char offset in a file from line-based char offset.

    :param line: line number
    :param offset: character offset in line
    :param line_lengths: line lengths list, e.g. from calculate_line_lengths
    :return: absolute character offset
    """
    start = 0
    for line_length in line_lengths[:line]:
        start += line_length
    return start + offset


def calculate_line_lengths(filename: str) -> List[int]:
    """Calculates line lengths for each line in a file.

    :param filename: path to the inspected file
    :return: list of line lengths with indices representing 1-based line numbers
    """

    lines = Path(filename).read_text().splitlines(keepends=True)
    result = [0]
    for line in lines:
        result.append(len(line))
    return result


def calculate_line_offsets(file: Path) -> List[int]:
    """Calculates character offsets for each line in a file.

    Indices correspond to the line numbers. For example, if first 4 lines
    contain 100 characters (including line breaks),result[5] will be 100.
    result[0] = result[1] = 0

    :param file: path to the inspected file
    :return: list of line offsets with indices representing 1-based line numbers
    """
    lines = Path(file).read_text().splitlines(keepends=True)
    offset = 0
    result = [0]
    for line in lines:
        result.append(offset)
        offset += len(line)
    return result


def format_input_file(file):
    lines = Path(file).read_text().splitlines(keepends=True)
    temp_file = Path("temp_file")
    i = 1
    text = ""
    for line in lines:
        text = text + str(i) + ":" + line
        i = i + 1
    temp_file.write_text(text)
    return temp_file
