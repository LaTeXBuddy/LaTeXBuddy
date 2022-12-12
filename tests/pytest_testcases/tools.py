from __future__ import annotations

import subprocess


def get_command_string(cmd):
    """Constructs a command string from a tuple of arguments.

    :param cmd: tuple of command line arguments
    :return: the command string
    """
    command = ""
    for arg in cmd:
        command += str(arg) + " "
    return command.strip()


def execute_and_collect(*cmd, encoding="ISO8859-1"):
    """Executes a terminal command with subprocess.

    :param cmd: command name and arguments
    :param encoding: output encoding
    :return: command output
    """

    command = get_command_string(cmd)

    error_list = subprocess.Popen(
        [command],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    out, err_out = error_list.communicate()
    return out.decode(encoding)
