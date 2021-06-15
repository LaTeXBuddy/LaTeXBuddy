"""This module contains various utility tools."""

import os
import re
import signal
import subprocess
import sys
import traceback

from logging import Logger
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from latexbuddy.exceptions import ExecutableNotFoundError
from latexbuddy.messages import not_found


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


def find_executable(
    name: str,
    to_install: Optional[str] = None,
    logger: Optional[Logger] = None,
    log_errors: bool = True,
) -> str:
    """Finds path to an executable. If the executable can not be located, an error
    message is logged to the specified logger, otherwise the executable's path is logged
    as a debug message.

    This uses 'which', i.e. the executable should at least be in user's $PATH

    :param name: executable name
    :param to_install: correct name of the program or project which the requested
                       executable belongs to (used in log messages)
    :param logger: custom logger to be used for logging debug/error messages
    :param log_errors: specifies whether or not this method should log an error message,
                       if the executable can not be located; if this is False, a debug
                       message will be logged instead
    :return: path to the executable
    :raises FileNotFoundError: if the executable couldn't be found
    """

    if logger is None:
        # importing this here to avoid circular import error
        from latexbuddy import __logger as root_logger

        logger = root_logger.getChild("Tools")

    result = execute("which", name)

    if not result or "not found" in result:

        if log_errors:
            logger.error(
                not_found(name, to_install if to_install is not None else name)
            )
        else:
            logger.debug(
                f"could not find executable '{name}' "
                f"({to_install if to_install is not None else name}) "
                f"in the system's PATH"
            )

        raise ExecutableNotFoundError(
            f"could not find executable '{name}' in system's PATH"
        )

    else:

        path_str = result.splitlines()[0]
        logger.debug(f"Found executable {name} at '{path_str}'.")
        return path_str


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
    error_message: str = "An error occurred while executing lambda function",
    traceback_log_level: Optional[str] = None,
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

        # importing this here to avoid circular import error
        from latexbuddy import __logger as root_logger

        logger = root_logger.getChild("Tools")

        logger.error(
            f"{error_message}:\n{e.__class__.__name__}: {getattr(e, 'message', e)}"
        )
        if traceback_log_level is not None:

            stack_trace = traceback.format_exc()

            if traceback_log_level == "DEBUG":
                logger.debug(stack_trace)
            elif traceback_log_level == "INFO":
                logger.info(stack_trace)
            elif traceback_log_level == "WARNING":
                logger.warning(stack_trace)
            elif traceback_log_level == "ERROR":
                logger.error(stack_trace)
            else:
                # use level DEBUG as default, in case of invalid value
                logger.debug(stack_trace)


def get_app_dir() -> Path:
    """Finds the directory for storing application data (mostly logs).

    This is a lightweight port of Click's mononymous function:
    https://github.com/pallets/click/blob/af0af571cbbd921d3974a0ff9cf58a4b26bb852b/src/click/utils.py#L412-L458

    :return: path of the application directory
    """

    from latexbuddy import __app_name__ as proper_name
    from latexbuddy import __name__ as unix_name

    # Windows
    if sys.platform.startswith("win"):
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata is not None:
            config_home = Path(localappdata)
        else:
            config_home = Path.home()

        app_dir = config_home / proper_name

    # macOS
    elif sys.platform.startswith("darwin"):
        config_home = Path.home() / "Library" / "Application Support"

        app_dir = config_home / proper_name

    # *nix
    else:
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home is not None:
            config_home = Path(xdg_config_home)
        else:
            config_home = Path.home() / ".config"

        app_dir = config_home / unix_name

    app_dir.mkdir(parents=True, exist_ok=True)

    return app_dir


def add_whitelist_console(whitelist_file, to_add):
    """
    TODO
    """
    with whitelist_file.open("a+") as file:
        file.write(to_add)
        file.write("\n")


def add_whitelist_from_file(whitelist_file, file_to_parse, lang):
    """
    TODO
    """
    lines = file_to_parse.read_text().splitlines(keepends=False)
    # TODO check if whitelist file and file to parse is path
    with whitelist_file.open("a+") as file:
        for line in lines:
            if line == "":
                continue
            file.write(lang + "_spelling_" + line)
            file.write("\n")
