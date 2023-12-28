# LaTeXBuddy LanguageTool checker
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
"""This module defines the connection between LaTeXBuddy and LanguageTool."""
from __future__ import annotations

import json
import logging
import re
import socket
import subprocess
import time
from contextlib import closing
from enum import Enum
from json import JSONDecodeError
from typing import Any
from typing import AnyStr
from typing import List
from typing import TYPE_CHECKING

import requests

import latexbuddy.tools
from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.exceptions import ExecutableNotFoundError
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from latexbuddy.texfile import TexFile

if TYPE_CHECKING:
    from subprocess import Popen

LOG = logging.getLogger(__name__)


class Mode(Enum):
    """Describes the LanguageTool mode.

    LanguageTool can be run as a command line program, a local server,
    or a remote server.
    """

    COMMANDLINE = "COMMANDLINE"
    LOCAL_SERVER = "LOCAL_SERVER"
    REMOTE_SERVER = "REMOTE_SERVER"


def find_languagetool_command_prefix() -> list[str]:
    """Find a valid LanguageTool executable and return the command prefix.

    This method finds either an executable named ``languagetool`` or
    the ``languagetool-commandline.jar`` file. In the case of the
    latter, it returns the path to the file prefixed with ``java``.

    :return: Prefix of the LanguageTool command
    """
    try:
        return [
            latexbuddy.tools.find_executable(
                "languagetool",
                "LanguageTool (CLI)",
                LOG,
                log_errors=False, ),
        ]
    except ExecutableNotFoundError:
        latexbuddy.tools.find_executable(
            "java", "JRE (Java Runtime Environment)", LOG,
        )

        return [
            "java",
            "-jar",
            latexbuddy.tools.find_executable(
                "languagetool-commandline.jar",
                "LanguageTool (CLI)",
                LOG,
            ),
        ]


def find_languagetool_server_prefix() -> list[str]:
    """Find a valid LanguageTool server executable and return the command
    prefix.

    This method finds either an executable named
    ``languagetool-server`` or the ``languagetool-server.jar`` file.
    In the case of the latter, it returns the path to the file prefixed
    with ``java``.

    :return: Prefix of the LanguageTool server command
    """
    try:
        return [
            latexbuddy.tools.find_executable(
                "languagetool-server",
                "LanguageTool (local server)",
                LOG,
                log_errors=False, ),
        ]
    except ExecutableNotFoundError:
        latexbuddy.tools.find_executable(
            "java", "JRE (Java Runtime Environment)", LOG,
        )

        return [
            "java",
            "-cp",
            latexbuddy.tools.find_executable(
                "languagetool-server.jar",
                "LanguageTool (local server)",
                LOG,
            ),
            "org.languagetool.server.HTTPServer",
        ]


class LanguageTool(Module):
    """Wraps the LanguageTool API calls to check files."""

    _REGEX_LANGUAGE_FLAG = re.compile(
        r"([a-zA-Z]{2,3})(?:[-_\s]([a-zA-Z]{2,3}))?",
    )

    def __init__(self) -> None:
        """Creates a LanguageTool checking module."""

        self.language = None

        self.disabled_rules = ""
        self.disabled_categories = ""

        self.remote_url_languages = None

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        """Runs the LanguageTool checks on a file and returns the results as a
        list.

        Requires LanguageTool (server) to be set up. Local or global
        servers can be used.

        :param config: the configuration options of the calling
            LaTeXBuddy instance
        :param file: LaTeX file to be checked (with built-in detex
            option)
        """

        cfg_mode = config.get_config_option_or_default(
            LanguageTool,
            "mode",
            "COMMANDLINE",
            verify_type=AnyStr,  # type: ignore
            verify_choices=[e.value for e in Mode],
        )

        try:
            self.mode = Mode(cfg_mode)
        except ValueError:
            self.mode = Mode.COMMANDLINE

        if self.mode == Mode.LOCAL_SERVER:
            self.local_server = LanguageToolLocalServer()
            self.local_server.start_local_server()

        elif self.mode == Mode.REMOTE_SERVER:
            # must include the port and api call (e.g. /v2/check)
            self.remote_url = config.get_config_option(
                LanguageTool,
                "remote_url_check",
                verify_type=AnyStr,  # type: ignore
                verify_regex="http(s?)://(\\S*)",
            )

            self.remote_url_languages = config.get_config_option_or_default(
                LanguageTool,
                "remote_url_languages",
                None,
                verify_type=AnyStr,  # type: ignore
                verify_regex="http(s?)://(\\S*)",
            )

        elif self.mode == Mode.COMMANDLINE:
            pass

        supported_languages = self.find_supported_languages()

        self.language = config.get_config_option_or_default(
            LatexBuddy,
            "language",
            None,
            verify_type=AnyStr,  # type: ignore
            verify_choices=supported_languages,
        )

        language_country = config.get_config_option_or_default(
            LatexBuddy,
            "language_country",
            None,
            verify_type=AnyStr,  # type: ignore
        )

        if (
            self.language is not None
            and language_country is not None
            and self.language + "-" + language_country in supported_languages
        ):
            self.language = self.language + "-" + language_country

        self.find_disabled_rules(config)

        return self.check_tex(file)

    def find_supported_languages(self) -> list[str]:
        """Acquires a list of supported languages from the version of
        LanguageTool that is currently used."""

        if self.mode == Mode.COMMANDLINE:

            cmd = find_languagetool_command_prefix()
            cmd.append("--list")

            languagetool_output = subprocess.check_output(cmd, text=True)
            supported_languages = [
                lang.split(" ")[0]
                for lang in languagetool_output.splitlines()
            ]
            return list(
                filter(self.matches_language_regex, supported_languages),
            )

        if self.mode == Mode.LOCAL_SERVER:

            return self.lt_languages_get_request(
                f"http://localhost:{self.local_server.port}/v2/languages",
            )

        if self.mode == Mode.REMOTE_SERVER:

            if not self.remote_url_languages:
                return []

            return self.lt_languages_get_request(self.remote_url_languages)

        return []

    def matches_language_regex(self, language: str) -> bool:
        """Determines whether a given string is a language code by matching it
        against a regular expression."""

        return self._REGEX_LANGUAGE_FLAG.fullmatch(language) is not None

    def find_languagetool_command_prefix(self) -> list[str]:
        """Finds the prefix of the shell command executing LanguageTool in the
        commandline."""

        latexbuddy.tools.find_executable(
            "java", "JRE (Java Runtime Environment)", LOG,
        )

        try:
            result = latexbuddy.tools.find_executable(
                "languagetool",
                "LanguageTool (CLI)",
                LOG,
                log_errors=False,
            )
            executable_source = "native"

        except ExecutableNotFoundError:

            result = latexbuddy.tools.find_executable(
                "languagetool-commandline.jar",
                "LanguageTool (CLI)",
                LOG,
            )
            executable_source = "java"

        command_prefix = []

        if executable_source == "java":
            command_prefix.append("java")
            command_prefix.append("-jar")

        command_prefix.append(result)

        return command_prefix

    def find_disabled_rules(self, config: ConfigLoader) -> None:
        """Reads all disabled rules and categories from the specified
        configuration and saves the result in the instance.

        :param config: configuration options to be read
        """

        self.disabled_rules = ",".join(
            config.get_config_option_or_default(
                LanguageTool,
                "disabled-rules",
                [],
                verify_type=List[str],
            ),
        )

        self.disabled_categories = ",".join(
            config.get_config_option_or_default(
                LanguageTool,
                "disabled-categories",
                [],
                verify_type=List[str],
            ),
        )

    def check_tex(self, file: TexFile) -> list[Problem]:
        """Runs the LanguageTool checks on a file.

        :param file: the file to run checks on
        """

        raw_problems: dict[str, Any] = {}

        if self.mode == Mode.LOCAL_SERVER:
            raw_problems = self.lt_post_request(
                file,
                "http://localhost:" f"{self.local_server.port}" "/v2/check",
            )

        elif self.mode == Mode.REMOTE_SERVER:
            raw_problems = self.lt_post_request(file, self.remote_url)

        elif self.mode == Mode.COMMANDLINE:
            raw_problems = self.execute_commandline_request(file)

        return self.format_errors(raw_problems, file)

    def lt_post_request(
        self,
        file: TexFile,
        server_url: str,
    ) -> dict[str, Any]:
        """Send a POST request to the LanguageTool server to check the text.

        :param file: TexFile object representing the file to be checked
        :param server_url: URL of the LanguageTool server
        :return: server's response
        """
        request_data = {
            "text": file.plain,
        }

        if self.language:
            request_data["language"] = self.language
        else:
            request_data["language"] = "auto"

        if self.disabled_rules:
            request_data["disabledRules"] = self.disabled_rules

        if self.disabled_categories:
            request_data["disabledCategories"] = self.disabled_categories

        response = requests.post(url=server_url, data=request_data, timeout=60)

        try:
            return response.json()
        except JSONDecodeError:
            LOG.error(
                f"Could not decode the following POST response in JSON format:"
                f" {response.text}",
            )
            return {}

    def lt_languages_get_request(self, server_url: str) -> list[str]:
        """Sends a GET request to the specified URL in order to retrieve a JSON
        formatted list of supported languages by the server.

        If the response format is invalid, this method will most likely
        fail with an exception.
        """

        response_json = requests.get(server_url, timeout=60).json()

        return list(
            filter(
                self.matches_language_regex,
                [entry["longCode"] for entry in response_json],
            ),
        )

    def execute_commandline_request(self, file: TexFile) -> dict[str, Any]:
        """Execute the LanguageTool command line app to check the text.

        :param file: TexFile object representing the file to be checked
        :return: app's response
        """

        command: list[str] = find_languagetool_command_prefix()
        command.append("--json")
        if self.language:
            command.append("-l")
            command.append(self.language)
        else:
            command.append("--autoDetect")
        if self.disabled_rules:
            command.append("--disable")
            command.append(self.disabled_rules)
        if self.disabled_categories:
            command.append("--disablecategories")
            command.append(self.disabled_categories)

        output = subprocess.check_output(
            (
                *command,
                file.plain_file,
            ),
            text=True,
        )

        if len(output) > 0:
            output = output[output.find("{"):]

        try:
            json_output = json.loads(output)
        except json.decoder.JSONDecodeError:
            json_output = {}

        return json_output

    @staticmethod
    def format_errors(
        raw_problems: dict[str, Any],
        file: TexFile,
    ) -> list[Problem]:
        """Parses LanguageTool errors and converts them to LaTeXBuddy Error
        objects.

        :param raw_problems: LanguageTool's error output
        :param file: TexFile object representing the file to be checked
        """

        problems: list[Problem] = []

        if raw_problems is None or len(raw_problems) == 0:
            return problems

        tool_name = raw_problems["software"]["name"]

        for match in raw_problems["matches"]:

            context = match["context"]
            context_offset = context["offset"]
            context_end = context["length"] + context_offset
            text = context["text"][context_offset:context_end]
            location = file.get_position_in_tex(match["offset"])

            problem_type = "grammar"

            if match["rule"]["category"]["id"] == "TYPOS":
                problem_type = "spelling"

            problems.append(
                Problem(
                    position=location,
                    text=text,
                    checker=LanguageTool,
                    p_type=match["rule"]["id"],
                    file=file.tex_file,
                    severity=ProblemSeverity.ERROR,
                    category=problem_type,
                    description=match["rule"]["description"],
                    context=(
                        match["context"]["text"][:context_offset],
                        match["context"]["text"][context_end:],
                    ),
                    suggestions=LanguageTool.parse_error_replacements(
                        match["replacements"],
                    ),
                    key=tool_name + "_" + match["rule"]["id"],
                ),
            )

        return problems

    @staticmethod
    def parse_error_replacements(
        json_replacements: list[dict[str, Any]],
        max_elements: int = 5,
    ) -> list[str]:
        """Converts LanguageTool's replacements to LaTeXBuddy suggestions list.

        :param json_replacements: list of LT's replacements for a
            particular word
        :param max_elements: max amount of proposed replacements for the
            given error
        :return: list of string values of said replacements
        """
        output = []

        for entry in json_replacements:
            output.append(entry["value"])

            if len(output) >= max_elements:
                break

        return output


class LanguageToolLocalServer:
    """Defines an instance of a local LanguageTool deployment."""

    __DEFAULT_PORT = 8081
    __SERVER_REQUEST_TIMEOUT = 1  # in seconds
    __SERVER_MAX_ATTEMPTS = 20

    def __init__(self) -> None:
        self.port = self.__DEFAULT_PORT
        self.server_process: Popen[bytes] | None = None

    def __del__(self) -> None:
        self.stop_local_server()

    def start_local_server(self, port: int = __DEFAULT_PORT) -> int:
        """Starts the LanguageTool server locally.

        :param port: port for the server to listen at
        :return: the actual port of the server
        """

        if self.server_process:
            return -1

        self.port = self.find_free_port(port)

        self.server_process = subprocess.Popen(
            (
                *find_languagetool_server_prefix(),
                "--port",
                str(self.port),
            ),
            start_new_session=True,
        )

        self.wait_till_server_up()

        return self.port

    def wait_till_server_up(self) -> None:
        """Waits for the LanguageTool server to start.

        :raises ConnectionError: if server didn't start
        """

        attempts = 0
        up = False

        while not up and attempts < self.__SERVER_MAX_ATTEMPTS:
            try:
                requests.post(
                    f"http://localhost:{self.port}/v2/check",
                    timeout=self.__SERVER_REQUEST_TIMEOUT,
                )
                up = True

            except requests.RequestException:
                up = False
                attempts += 1
                time.sleep(0.5)

        if not up:
            _msg = "Could not connect to local server."
            raise ConnectionError(_msg)

    def stop_local_server(self) -> None:
        """Stops the local LanguageTool server process."""

        if not self.server_process:
            return

        latexbuddy.tools.kill_background_process(self.server_process)
        self.server_process = None

    @staticmethod
    def find_free_port(port: int | None = None) -> int:
        """Tries to find a free port for the LanguageTool server.

        :param port: port to check first
        :return: a free port that the LanguageTool server can listen at
        """

        if port and not LanguageToolLocalServer.is_port_in_use(port):
            return port

        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("localhost", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    @staticmethod
    def is_port_in_use(port: int) -> bool:
        """Checks if a port is already in use.

        :param port: port to check
        :return: True if port already in use, False otherwise
        """

        if not port:
            return True

        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            return s.connect_ex(("localhost", port)) == 0
