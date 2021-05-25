"""This module contains various utility tools."""

import os
import re
import signal
import subprocess
import sys
import traceback

from io import StringIO
from pathlib import Path
from typing import Callable, List, Optional, Tuple

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


location_re = re.compile(r"line (\d+), column (\d+)")


def absolute_to_linecol(text: str, position: int) -> Tuple[int, int, List[int]]:
    """Calculates line and column number for an absolute character position.

    :param text: text of file to find line:col position for
    :param position: absolute 0-based character position
    :return: line number, column number, line offsets
    """
    line_offsets = get_line_offsets(text)
    line = 0  # [0, ...]
    while position >= line_offsets[line]:
        line += 1

    # translate_numbers expects 1-based column number
    # however, line_offsets is 0-based
    column = position - line_offsets[line - 1] + 1

    return line, column, line_offsets


def get_line_offsets(text: str) -> List[int]:
    """Calculates character offsets for each line in the file.

    Indices correspond to the line numbers, but are 0-based. For example, if first
    4 lines contain 100 characters (including line breaks), `result[4]` will be 100.
    `result[0]` = 0.

    This is a port of YaLaFi's get_line_starts() function.

    :param text: contents of file to find offsets for
    :return: list of line offsets with indices representing 0-based line numbers
    """
    lines = text.splitlines(keepends=True)
    offset = 0
    result = []
    for line in lines:
        result.append(offset)
        offset += len(line)
    result.append(offset)  # last line

    return result


def is_binary(file_bytes: bytes) -> bool:
    """Detects whether the bytes of a file contain binary code or not.

    For correct detection, it is recommended, that at least 1024 bytes were read.

    Sources:
      * https://stackoverflow.com/a/7392391/4735420
      * https://github.com/file/file/blob/f2a6e7cb7d/src/encoding.c#L151-L228

    :param file_bytes: bytes of a file
    :return: True, if the file is binary, False otherwise
    """
    textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F})
    return bool(file_bytes.translate(None, textchars))


def execute_no_exceptions(
    function_call: Callable[[], None],
    error_message: str = "An error occurred while executing lambda function at",
) -> None:
    """Calls a function and catches any Exception that is raised during this.

    If an Exception is caught, the function is aborted and the error is printed to
    stderr, but as the Exception is caught, the program won't crash.

    :param function_call: function to be executed
    :param error_message: custom error message displayed in the console
    """

    try:
        function_call()
    except Exception as e:

        print(
            error_message + ":\n",
            f"{e.__class__.__name__}: {getattr(e, 'message', e)}",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
