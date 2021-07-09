"""This module defines the connection between LaTeXBuddy and LanguageTool."""

import json
import re
import socket
import time

from contextlib import closing
from enum import Enum
from json import JSONDecodeError
from logging import Logger
from typing import AnyStr, Dict, List, Optional

import requests

import latexbuddy.tools as tools

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.exceptions import ExecutableNotFoundError
from latexbuddy.modules import Module
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


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

    _REGEX_LANGUAGE_FLAG = re.compile(r"([a-zA-Z]{2,3})(?:[-_\s]([a-zA-Z]{2,3}))?")

    def __init__(self):
        """Creates a LanguageTool checking module."""

        self.mode = None
        self.language = None

        self.disabled_rules = None
        self.disabled_categories = None

        self.local_server = None
        self.remote_url = None
        self.remote_url_languages = None
        self.lt_console_command = None

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        """Runs the LanguageTool checks on a file and returns the results as a list.

        Requires LanguageTool (server) to be set up.
        Local or global servers can be used.

        :param config: the configuration options of the calling LaTeXBuddy instance
        :param file: LaTeX file to be checked (with built-in detex option)
        """

        cfg_mode = config.get_config_option_or_default(
            LanguageTool,
            "mode",
            "COMMANDLINE",
            verify_type=AnyStr,
            verify_choices=[e.value for e in Mode],
        )

        try:
            self.mode = Mode(cfg_mode)
        except ValueError:
            self.mode = Mode.COMMANDLINE

        if self.mode == Mode.LOCAL_SERVER:
            self.local_server = LanguageToolLocalServer(self.logger)
            self.local_server.start_local_server()

        elif self.mode == Mode.REMOTE_SERVER:
            # must include the port and api call (e.g. /v2/check)
            self.remote_url = config.get_config_option(
                LanguageTool,
                "remote_url_check",
                verify_type=AnyStr,
                verify_regex="http(s?)://(\\S*)",
            )

            self.remote_url_languages = config.get_config_option_or_default(
                LanguageTool,
                "remote_url_languages",
                None,
                verify_type=AnyStr,
                verify_regex="http(s?)://(\\S*)",
            )

        elif self.mode == Mode.COMMANDLINE:
            pass

        supported_languages = self.find_supported_languages()

        self.language = config.get_config_option_or_default(
            LatexBuddy,
            "language",
            None,
            verify_type=AnyStr,
            verify_choices=supported_languages,
        )

        language_country = config.get_config_option_or_default(
            LatexBuddy,
            "language_country",
            None,
            verify_type=AnyStr,
        )

        if (
            self.language is not None
            and language_country is not None
            and self.language + "-" + language_country in supported_languages
        ):
            self.language = self.language + "-" + language_country

        self.find_disabled_rules(config)

        result = self.check_tex(file)

        return result

    def find_supported_languages(self) -> List[str]:
        """
        Acquires a list of supported languages from the version of LanguageTool that
        is currently used.
        """

        if self.mode == Mode.COMMANDLINE:

            cmd = self.find_languagetool_command_prefix()
            cmd.append("--list")

            result = tools.execute(*cmd)

            supported_languages = [lang.split(" ")[0] for lang in result.splitlines()]
            supported_languages = list(
                filter(self.matches_language_regex, supported_languages)
            )

            return supported_languages

        elif self.mode == Mode.LOCAL_SERVER:

            return self.lt_languages_get_request(
                f"http://localhost:{self.local_server.port}/v2/languages"
            )

        elif self.mode == Mode.REMOTE_SERVER:

            if not self.remote_url_languages:
                return []

            return self.lt_languages_get_request(self.remote_url_languages)

        else:
            return []

    def matches_language_regex(self, language: str) -> bool:
        """
        Determines whether a given string is a language code by matching it against a
        regular expression.
        """

        return self._REGEX_LANGUAGE_FLAG.fullmatch(language) is not None

    def find_languagetool_command_prefix(self) -> List[str]:
        """
        Finds the prefix of the shell command executing LanguageTool in the commandline.
        """

        tools.find_executable("java", "JRE (Java Runtime Environment)", self.logger)

        try:
            result = tools.find_executable(
                "languagetool", "LanguageTool (CLI)", self.logger, log_errors=False
            )
            executable_source = "native"

        except ExecutableNotFoundError:

            result = tools.find_executable(
                "languagetool-commandline.jar", "LanguageTool (CLI)", self.logger
            )
            executable_source = "java"

        lt_path = result
        command_prefix = []

        if executable_source == "java":
            command_prefix.append("java")
            command_prefix.append("-jar")

        command_prefix.append(lt_path)

        return command_prefix

    def find_languagetool_command(self) -> None:
        """Searches for the LanguageTool command line app.

        This method also checks if Java is installed.
        """

        self.lt_console_command = self.find_languagetool_command_prefix()

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
        """
        Reads all disabled rules and categories from the specified configuration and
        saves the result in the instance.

        :param config: configuration options to be read
        """

        self.disabled_rules = ",".join(
            config.get_config_option_or_default(
                LanguageTool, "disabled-rules", [], verify_type=List[str]
            )
        )

        self.disabled_categories = ",".join(
            config.get_config_option_or_default(
                LanguageTool, "disabled-categories", [], verify_type=List[str]
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

        try:
            return response.json()
        except JSONDecodeError:
            self.logger.error(
                f"Could not decode the following POST response in JSON format: "
                f"{response.text}"
            )
            return None

    def lt_languages_get_request(self, server_url: str) -> List[str]:
        """
        Sends a GET request to the specified URL in order to retrieve a JSON formatted
        list of supported languages by the server. If the response format is invalid,
        this method will most likely fail with an exception.
        """

        response_json = requests.get(server_url).json()

        supported_languages = [entry["longCode"] for entry in response_json]
        supported_languages = list(
            filter(self.matches_language_regex, supported_languages)
        )

        return supported_languages

    def execute_commandline_request(self, file: TexFile) -> Optional[Dict]:
        """Execute the LanguageTool command line app to check the text.

        :param file: TexFile object representing the file to be checked
        :return: app's response
        """

        if file is None:
            return None

        self.find_languagetool_command()

        # cloning list to in order to append the file name
        # w/o changing lt_console_command
        cmd = list(self.lt_console_command)
        cmd.append(str(file.plain_file))

        output = tools.execute_no_errors(*cmd, encoding="utf_8")

        if len(output) > 0:
            output = output[output.find("{") :]

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

    __DEFAULT_PORT = 8081
    __SERVER_REQUEST_TIMEOUT = 1  # in seconds
    __SERVER_MAX_ATTEMPTS = 20

    def __init__(self, logger: Logger):
        self.lt_path = None
        self.lt_server_command = None
        self.server_process = None
        self.port = None

        self.logger = logger

    def __del__(self):
        self.stop_local_server()

    def get_server_run_command(self) -> None:
        """Searches for the LanguageTool server executable.

        This method also checks if Java is installed.
        """

        tools.find_executable("java", "JRE (Java Runtime Environment)", self.logger)

        try:
            result = tools.find_executable(
                "languagetool-server",
                "LanguageTool (local server)",
                self.logger,
                log_errors=False,
            )
            executable_source = "native"

        except ExecutableNotFoundError:

            result = tools.find_executable(
                "languagetool-server.jar", "LanguageTool (local server)", self.logger
            )
            executable_source = "java"

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

    def start_local_server(self, port: int = __DEFAULT_PORT) -> int:
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
