"""This module contains various utility tools."""
from __future__ import annotations

import logging
import os
import re
import signal
import subprocess
import traceback
from argparse import Namespace
from logging import Logger
from pathlib import Path
from typing import Callable

from platformdirs import PlatformDirs

from latexbuddy.exceptions import ExecutableNotFoundError
from latexbuddy.messages import not_found
from latexbuddy.messages import path_not_found

LOG = logging.getLogger(__name__)

dirs = PlatformDirs(
    appname="LaTeXBuddy",
    appauthor=False,
)

inc_re = re.compile(r"\\include{(?P<file_name>.*)}")
inp_re = re.compile(r"\\input{(?P<file_name>.*)}")


def execute(*cmd: str, encoding: str = "ISO8859-1") -> str:
    """Executes a terminal command with subprocess.

    See usage example in latexbuddy.aspell.

    :param cmd: command name and arguments
    :param encoding: output encoding
    :return: command output
    """

    command = get_command_string(cmd)

    LOG.debug(f"Executing '{command}'")

    error_list = subprocess.Popen(
        [command],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    out, err_out = error_list.communicate()
    return out.decode(encoding)


def execute_background(*cmd: str) -> subprocess.Popen:
    """Executes a terminal command in background.

    :param cmd: command name and arguments
    :return: subprocess instance of the executed command
    """
    command = get_command_string(cmd)

    LOG.debug(f"Executing '{command}' in the background")

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

    LOG.debug(f"Executing '{command}' (ignoring errors)")

    error_list = subprocess.Popen(
        [command],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    out, err_out = error_list.communicate()
    return out.decode(encoding)


def get_command_string(cmd: tuple[str]) -> str:
    """Constructs a command string from a tuple of arguments.

    :param cmd: tuple of command line arguments
    :return: the command string
    """
    command = ""
    for arg in cmd:
        command += str(arg) + " "
    return command.strip()


def find_executable(
    name: str,
    to_install: str | None = None,
    err_logger: Logger = LOG,
    log_errors: bool = True,
) -> str:
    """Finds path to an executable. If the executable can not be located, an
    error message is logged to the specified logger, otherwise the executable's
    path is logged as a debug message.

    This uses 'which', i.e. the executable should at least be in user's $PATH

    :param name: executable name
    :param to_install: correct name of the program or project which the requested
                       executable belongs to (used in log messages)
    :param err_logger: custom logger to be used for logging debug/error messages
    :param log_errors: specifies whether or not this method should log an error message,
                       if the executable can not be located; if this is False, a debug
                       message will be logged instead
    :return: path to the executable
    :raises FileNotFoundError: if the executable couldn't be found
    """

    result = execute("which", name)

    if not result or "not found" in result:

        if log_errors:
            err_logger.error(
                not_found(name, to_install if to_install is not None else name),
            )
        else:
            err_logger.debug(
                f"could not find executable '{name}' "
                f"({to_install if to_install is not None else name}) "
                f"in the system's PATH",
            )

        raise ExecutableNotFoundError(
            f"could not find executable '{name}' in system's PATH",
        )

    else:

        path_str = result.splitlines()[0]
        err_logger.debug(f"Found executable {name} at '{path_str}'.")
        return path_str


location_re = re.compile(r"line (\d+), column (\d+)")


def absolute_to_linecol(text: str, position: int) -> tuple[int, int, list[int]]:
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


def get_line_offsets(text: str) -> list[int]:
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
    textchars = bytearray({7, 8, 9, 10, 12, 13, 27}
                          | set(range(0x20, 0x100)) - {0x7F})
    return bool(file_bytes.translate(None, textchars))


def execute_no_exceptions(
    function_call: Callable[[], None],
    error_message: str = "An error occurred while executing lambda function",
    traceback_log_level: str | None = None,
) -> None:
    """Calls a function and catches any Exception that is raised during this.

    If an Exception is caught, the function is aborted and the error is logged, but as
    the Exception is caught, the program won't crash.

    :param function_call: function to be executed
    :param error_message: custom error message displayed in the console
    :param traceback_log_level: sets the log_level that is used to log the error
                                traceback. If it is None, no traceback will be logged.
                                Valid values are: "DEBUG", "INFO", "WARNING", "ERROR"
    """

    try:
        function_call()
    except Exception as e:

        LOG.error(
            f"{error_message}:\n{e.__class__.__name__}: {getattr(e, 'message', e)}",
        )
        if traceback_log_level is not None:

            stack_trace = traceback.format_exc()

            if traceback_log_level == "DEBUG":
                LOG.debug(stack_trace)
            elif traceback_log_level == "INFO":
                LOG.info(stack_trace)
            elif traceback_log_level == "WARNING":
                LOG.warning(stack_trace)
            elif traceback_log_level == "ERROR":
                LOG.error(stack_trace)
            else:
                # use level DEBUG as default, in case of invalid value
                LOG.debug(stack_trace)


def get_all_paths_in_document(file_path: Path) -> list[Path]:
    """Checks files that are included in a file.

    If the file includes more files, these files will also be checked.

    :param file_path:a string, containing file path
    :return: the files to check
    """
    unchecked_files = []
    checked_files = []
    unchecked_files.append(file_path)
    root_dir = str(file_path.parent)

    while len(unchecked_files) > 0:
        unchecked_file = convert_file_to_absolute(unchecked_files, root_dir)
        try:
            lines = unchecked_file.read_text().splitlines(keepends=False)
        except FileNotFoundError:
            LOG.error(
                path_not_found(
                    "the checking of imports", unchecked_file,
                ),
            )
            continue
        except Exception as e:  # If the file cannot be found it is already removed
            error_message = "Error while searching for files"
            LOG.error(
                f"{error_message}:\n{e.__class__.__name__}: {getattr(e, 'message', e)}",
            )
            continue

        unchecked_files = match_lines(lines, unchecked_files, checked_files)

        checked_files.append(unchecked_file)

    return checked_files


def convert_file_to_absolute(unchecked_files: list[Path], root_dir: str) -> Path:
    """Converts a relative path to an absolute if needed.

    :param unchecked_files: the list of unchecked_files
    :param root_dir: the root directory
    :return: the absolute path
    """
    unchecked_file = unchecked_files.pop(0)
    if not (str(unchecked_file)[:2] == "~/" or str(unchecked_file)[0] == "/"):
        unchecked_file = Path(root_dir + "/" + str(unchecked_file))
    return texify_path(str(unchecked_file))


def match_lines(
    lines: list[str],
    unchecked_files: list[Path],
    checked_files: list[Path],
) -> list[Path]:
    """Matches the lines with the given regexes.

    :param lines: the lines
    :unchecked_files: the unchecked_files
    :checked_files: the checked_files
    :return: the unchecked_files
    """
    for line in lines:
        match_inc = inc_re.match(line)
        match_inp = inp_re.match(line)
        if match_inc:
            match = Path(match_inc.group("file_name"))
            if match not in unchecked_files and match not in checked_files:
                unchecked_files.append(match)
        if match_inp:
            match = Path(match_inp.group("file_name"))
            if match not in unchecked_files and match not in checked_files:
                unchecked_files.append(match)
    return unchecked_files


def texify_path(path: str) -> Path:
    """Adds .tex to a file path if needed.

    :param path: the path
    :return: the texified path
    """
    if not path.endswith(".tex"):
        if Path(path + ".tex").exists():
            return Path(path + ".tex")
    return Path(path)


def perform_whitelist_operations(args: Namespace):
    """Performs whitelist operations.

    :param args: the args
    """
    wl_file = args.whitelist if args.whitelist else Path("whitelist")

    if args.add_to_whitelist:
        add_whitelist_console(wl_file, args.add_to_whitelist)

    if args.whitelist_from_wordlist:
        add_whitelist_from_file(
            wl_file,
            Path(args.whitelist_from_wordlist[0]),
            args.whitelist_from_wordlist[1],
        )


def add_whitelist_console(whitelist_file, to_add):
    """Adds a list of keys to the Whitelist. Keys should be valid keys, ideally
    copied from LaTeXBuddy HTML Output.

    :param whitelist_file: Path to whitelist file
    :param to_add: list of keys
    """
    whitelist_entries = whitelist_file.read_text().splitlines()
    with whitelist_file.open("a+") as file:
        for key in to_add:
            if key not in whitelist_entries:
                whitelist_entries.append(key)
                file.write(key)
                file.write("\n")


def get_abs_path(path) -> Path:
    """Gets absolute path of a string.

    :param path: the path
    :return: the absolute path
    """
    path = str(path)
    if path[:2] == "~/" or path[0] == "/":
        return Path(path)
    p = Path(str(os.getcwd()) + "/" + str(path))
    if not p.is_file() or path[-4:] != ".tex":
        LOG.error(f"File {p} does not exist.")
    return p


def add_whitelist_from_file(whitelist_file, file_to_parse, lang):
    """Takes in a list of words and creates their respective keys, then adds
    them to whitelist. Words in the file_to_parse should all be from the same
    language. Each line represents a single Word.

    :param whitelist_file: Path to whitelist file
    :param file_to_parse: Path to wordlist
    :param lang: language of the words in the wordlist
    """
    lines = file_to_parse.read_text().splitlines(keepends=False)
    # TODO check if whitelist file and file to parse is path
    whitelist_entries = whitelist_file.read_text().splitlines()
    with whitelist_file.open("a+") as file:
        for line in lines:
            if line == "":
                continue
            key = lang + "_spelling_" + line
            if key not in whitelist_entries:
                whitelist_entries.append(key)
                file.write(key)
                file.write("\n")


class classproperty(property):
    """Provides a way to implement a python property with class-level
    accessibility."""

    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()
