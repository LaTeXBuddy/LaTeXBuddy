# LaTeXBuddy tests
# Copyright (C) 2021-2022  LaTeXBuddy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
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
