"""This module defines the connection between LaTeXBuddy and LanguageTool."""

import json
import socket
import time

from contextlib import closing
from enum import Enum
from typing import Dict, List, Optional

import requests

import latexbuddy.tools as tools

from latexbuddy import TexFile
from latexbuddy import __logger as root_logger
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.messages import not_found
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity


class Mode(Enum):
    """Describes the LanguageTool mode.

    LanguageTool can be run as a command line program, a local server, or a remote
    server.
    """

    COMMANDLINE = "COMMANDLINE"
    LOCAL_SERVER = "LOCAL_SERVER"
    REMOTE_SERVER = "REMOTE_SERVER"


class LanguageTool(Module):
    """Wraps the LanguageTool API calls to check files."""

    __logger = root_logger.getChild("LanguageTool")

    _LANGUAGE_MAP = {"de": "de-DE", "en": "en-GB"}

    def __init__(self):
        """Creates a LanguageTool checking module."""

        self.mode = None
        self.language = None

        self.disabled_rules = None
        self.disabled_categories = None

        self.local_server = None
        self.remote_url = None
        self.lt_console_command = None

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        """Runs the LanguageTool checks on a file and returns the results as a list.

        Requires LanguageTool (server) to be set up.
        Local or global servers can be used.

        :param config: configurations of the LaTeXBuddy instance
        :param file: the file to run checks on
        """
        start_time = time.perf_counter()

        try:
            self.language = LanguageTool._LANGUAGE_MAP[
                config.get_config_option_or_default("buddy", "language", None)
            ]
        except KeyError:
            self.language = None

        self.find_disabled_rules(config)

        cfg_mode = config.get_config_option_or_default(
            "LanguageTool", "mode", "COMMANDLINE"
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
            self.remote_url = config.get_config_option("LanguageTool", "remote_url")

        elif self.mode == Mode.COMMANDLINE:
            self.find_languagetool_command()

        result = self.check_tex(file)

        self.__logger.debug(
            f"LanguageTool finished after {round(time.perf_counter() - start_time, 2)} seconds"
        )
        return result

    def find_languagetool_command(self) -> None:
        """Searches for the LanguageTool command line app.

        This method also checks if Java is installed.
        """
        try:
            tools.find_executable("java")
        except FileNotFoundError:
            self.__logger.error(not_found("java", "JRE (Java Runtime Environment)"))

        try:
            result = tools.find_executable("languagetool")
            executable_source = "native"
        except FileNotFoundError:
            try:
                result = tools.find_executable("$LTJAR")
                executable_source = "java"
            except FileNotFoundError:
                self.__logger.error(
                    not_found("languagetool-commandline.jar", "LanguageTool CLI")
                )

                raise FileNotFoundError("Unable to find languagetool installation!")

        lt_path = result
        self.lt_console_command = []

        if executable_source == "java":
            self.lt_console_command.append("java")
            self.lt_console_command.append("-jar")

        self.lt_console_command.append(lt_path)
        self.lt_console_command.append("--json")

        if self.language:
            self.lt_console_command.append("-l")
            self.lt_console_command.append(self.language)
        else:
            self.lt_console_command.append("--autoDetect")

        if self.disabled_rules:
            self.lt_console_command.append("--disable")
            self.lt_console_command.append(self.disabled_rules)

        if self.disabled_categories:
            self.lt_console_command.append("--disablecategories")
            self.lt_console_command.append(self.disabled_categories)

    def find_disabled_rules(self, config: ConfigLoader) -> None:

        self.disabled_rules = ",".join(
            config.get_config_option_or_default("LanguageTool", "disabled-rules", [])
        )

        self.disabled_categories = ",".join(
            config.get_config_option_or_default(
                "LanguageTool", "disabled-categories", []
            )
        )

        if self.disabled_rules == "":
            self.disabled_rules = None

        if self.disabled_categories == "":
            self.disabled_categories = None

    def check_tex(self, file: TexFile) -> List[Problem]:
        """Runs the LanguageTool checks on a file.

        :param file: the file to run checks on
        """

        raw_problems = None

        if self.mode == Mode.LOCAL_SERVER:
            raw_problems = self.lt_post_request(
                file, "http://localhost:" f"{self.local_server.port}" "/v2/check"
            )

        elif self.mode == Mode.REMOTE_SERVER:
            raw_problems = self.lt_post_request(file, self.remote_url)

        elif self.mode == Mode.COMMANDLINE:
            raw_problems = self.execute_commandline_request(file)

        return self.format_errors(raw_problems, file)

    def lt_post_request(self, file: TexFile, server_url: str) -> Optional[Dict]:
        """Send a POST request to the LanguageTool server to check the text.

        :param file: TexFile object representing the file to be checked
        :param server_url: URL of the LanguageTool server
        :return: server's response
        """
        if file is None:
            return None

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

        response = requests.post(url=server_url, data=request_data)
        return response.json()

    def execute_commandline_request(self, file: TexFile) -> Optional[Dict]:
        """Execute the LanguageTool command line app to check the text.

        :param file: TexFile object representing the file to be checked
        :return: app's response
        """

        if file is None:
            return None

        # cloning list to in order to append the file name
        # w/o changing lt_console_command
        cmd = list(self.lt_console_command)
        cmd.append(str(file.plain_file))

        output = tools.execute_no_errors(*cmd, encoding="utf_8")

        try:
            json_output = json.loads(output)
        except json.decoder.JSONDecodeError:
            json_output = json.loads("{}")

        return json_output

    @staticmethod
    def format_errors(raw_problems: Dict, file: TexFile) -> List[Problem]:
        """Parses LanguageTool errors and converts them to LaTeXBuddy Error objects.

        :param raw_problems: LanguageTool's error output
        :param file: TexFile object representing the file to be checked
        """

        problems = []

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
                    checker=tool_name,
                    cid=match["rule"]["id"],
                    file=file.tex_file,
                    severity=ProblemSeverity.ERROR,
                    category=problem_type,
                    description=match["rule"]["description"],
                    context=(
                        match["context"]["text"][:context_offset],
                        match["context"]["text"][context_end:],
                    ),
                    suggestions=LanguageTool.parse_error_replacements(
                        match["replacements"]
                    ),
                    key=tool_name + "_" + match["rule"]["id"],
                )
            )

        return problems

    @staticmethod
    def parse_error_replacements(
        json_replacements: List[Dict], max_elements: int = 5
    ) -> List[str]:
        """Converts LanguageTool's replacements to LaTeXBuddy suggestions list.

        :param json_replacements: list of LT's replacements for a particular word
        :param max_elements: Caps the number of replacements for the given error
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

    _DEFAULT_PORT = 8081
    _SERVER_REQUEST_TIMEOUT = 1  # in seconds
    _SERVER_MAX_ATTEMPTS = 20

    def __init__(self):
        self.lt_path = None
        self.lt_server_command = None
        self.server_process = None
        self.port = None

    def __del__(self):
        self.stop_local_server()

    def get_server_run_command(self) -> None:
        """Searches for the LanguageTool server executable.

        This method also checks if Java is installed.
        """
        try:
            tools.find_executable("java")
        except FileNotFoundError:
            self.__logger.error(not_found("java", "JRE (Java Runtime Environment)"))

            raise FileNotFoundError("Unable to find Java runtime environment!")

        try:
            result = tools.find_executable("languagetool-server")
            executable_source = "native"
        except FileNotFoundError:
            try:
                result = tools.find_executable("languagetool-server.jar")
                executable_source = "java"
            except FileNotFoundError:
                self.__logger.error(
                    not_found("languagetool-server.jar", "LanguageTool Server")
                )

                raise FileNotFoundError("Unable to find languagetool installation!")

        self.lt_path = result

        if executable_source == "java":
            self.lt_server_command = [
                "java",
                "-cp",
                self.lt_path,
                "org.languagetool.server.HTTPServer",
            ]

        elif executable_source == "native":
            self.lt_server_command = [
                self.lt_path,
            ]

        self.lt_server_command.append("--port")
        self.lt_server_command.append(str(self.port))

    def start_local_server(self, port: int = _DEFAULT_PORT) -> int:
        """Starts the LanguageTool server locally.

        :param port: port for the server to listen at
        :return: the actual port of the server
        """

        if self.server_process:
            return -1

        self.port = self.find_free_port(port)

        self.get_server_run_command()

        self.server_process = tools.execute_background(*self.lt_server_command)

        self.wait_till_server_up()

        return self.port

    def wait_till_server_up(self) -> None:
        """Waits for the LanguageTool server to start.

        :raises ConnectionError: if server didn't start
        """

        attempts = 0
        up = False

        while not up and attempts < self._SERVER_MAX_ATTEMPTS:
            try:
                requests.post(
                    f"http://localhost:{self.port}/v2/check",
                    timeout=self._SERVER_REQUEST_TIMEOUT,
                )
                up = True

            except requests.RequestException:
                up = False
                attempts += 1
                time.sleep(0.5)

        if not up:
            raise ConnectionError("Could not connect to local server.")

    def stop_local_server(self) -> None:
        """Stops the local LanguageTool server process."""

        if not self.server_process:
            return

        tools.kill_background_process(self.server_process)
        self.server_process = None

    @staticmethod
    def find_free_port(port: int = None) -> int:
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
