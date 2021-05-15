import os
import signal
import subprocess

from pathlib import Path
from typing import List, Tuple


# example usage in aspell.py
def execute(*cmd: str, encoding: str = "ISO8859-1") -> str:
    command = get_command_string(cmd)

    error_list = subprocess.Popen(
        [command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    out, err_out = error_list.communicate()
    return out.decode(encoding)


def execute_from_list(cmd: List[str], encoding: str = "ISO8859-1") -> str:
    return execute(*cmd, encoding=encoding)


def execute_background(*cmd: str) -> subprocess.Popen:
    command = get_command_string(cmd)

    process = subprocess.Popen(
        [command],
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )
    return process


def execute_background_from_list(cmd: List[str]) -> subprocess.Popen:
    return execute_background(*cmd)


def kill_background_process(process: subprocess.Popen):
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)


def execute_no_errors(*cmd: str, encoding: str = "ISO8859-1") -> str:
    command = get_command_string(cmd)

    error_list = subprocess.Popen(
        [command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    out, err_out = error_list.communicate()
    return out.decode(encoding)


def execute_no_errors_from_list(cmd: List[str], encoding: str = "ISO8859-1") -> str:
    return execute_no_errors(*cmd, encoding=encoding)


def get_command_string(cmd: Tuple[str]) -> str:
    command = ""
    for arg in cmd:
        command += arg + " "
    return command.strip()


def find_executable(name: str) -> str:
    result = execute("which", name)

    if not result or "not found" in result:
        raise FileNotFoundError(f"could not find {name} in system's PATH")
    else:
        return result.splitlines()[0]


def detex(file_to_detex):
    try:
        find_executable("detex")
    except FileNotFoundError:

        print("Could not find a valid detex installation on your system.")
        print("Please make sure you installed detex correctly and it is in your ")
        print("System's PATH.")

        print("For more information check the LaTeXBuddy manual.")

        raise FileNotFoundError("Unable to find detex installation!")

    detexed_file = file_to_detex + ".detexed"
    execute("detex", file_to_detex, " > ", detexed_file)
    return detexed_file


def calculate_line_offsets(filename: str) -> list[int]:
    """Calculates character offsets for each line in file.

    Indices correspond to the line numbers. For example, if first 4 lines
    contain 100 characters (including line breaks),result[5] will be 100.
    result[0] = result[1] = 0
    """
    lines = Path(filename).read_text().splitlines(keepends=True)
    offset = 0
    result = [0]
    for line in lines:
        result.append(offset)
        offset += len(line)
    return result


def calculate_line_lengths(filename):
    # file = open(filename, "r", encoding="utf-8", errors="ignore")
    # lines = file.readlines()
    # file.close()

    return list(
        map(lambda l: len(l), Path(filename).read_text().splitlines(keepends=True))
    )


def start_char(line, offset, line_lengths):
    start = 0
    for line_length in line_lengths[:line]:
        start += line_length
    return start + offset
