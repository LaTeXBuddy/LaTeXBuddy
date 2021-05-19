"""This module defines the connection between LaTeXBuddy and LanguageTool."""

import json
import socket
import sys
import time
import traceback

from contextlib import closing
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import requests

import latexbuddy.buddy as ltb
import latexbuddy.tools as tools

from latexbuddy.abs_module import InputFileType, Module
from latexbuddy.error_class import Error


class Mode(Enum):
    """Describes the LanguageTool mode.

    LanguageTool can be run as a command line program, a local server, or a remote
    server.
    """

    COMMANDLINE = "COMMANDLINE"
    LOCAL_SERVER = "LOCAL_SERVER"
    REMOTE_SERVER = "REMOTE_SERVER"


class LanguageToolModule(Module):
    """Wraps the LanguageTool API calls to check files."""

    _LANGUAGE_MAP = {"de": "de-DE", "en": "en-GB"}

    # TODO: implement whitelisting certain rules
    #       (exclude multiple whitespaces error by default)
    def __init__(self):
        """Creates a LanguageTool checking module."""

        self.buddy = None
        self.mode = None
        self.language = None

        self.local_server = None
        self.remote_url = None
        self.lt_console_command = None

        self.errors = None

    def get_input_file_type(self) -> InputFileType:
        """Specifies the required input file type for this module."""
        return InputFileType.DETEXED_FILE

    def run_module(self, buddy: ltb.LatexBuddy, file_path: Path) -> None:
        """Runs the LanguageTool checks on a file and saves the results in a LaTeXBuddy
        instance.

        Requires LanguageTool (server) to be set up.
        Local or global servers can be used.

        :param buddy: the LaTeXBuddy instance
        :param file_path: the file to run checks on
        """

        try:
            self.buddy = buddy

            try:
                self.language = LanguageToolModule._LANGUAGE_MAP[self.buddy.lang]
            except KeyError:
                self.language = None

            cfg_mode = buddy.cfg.get_config_option_or_default(
                "languagetool", "mode", "COMMANDLINE"
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
                self.remote_url = buddy.cfg.get_config_option(
                    "languagetool", "remote_url"
                )

            elif self.mode == Mode.COMMANDLINE:
                self.find_languagetool_command()

            self.errors = []
            self.check_tex(file_path)

        except Exception as e:

            print(
                f"An error occurred while executing latexbuddy:\n",
                f"{e.__class__.__name__}: {getattr(e, 'message', e)}",
                file=sys.stderr,
            )
            traceback.print_exc(file=sys.stderr)

    def fetch_errors(self) -> List[Error]:
        """Passes the accumulated errors on to the main LaTeXBuddy instance."""

        to_return = self.errors
        self.errors = []

        return to_return

    def find_languagetool_command(self) -> None:
        """Searches for the LanguageTool command line app.

        This method also checks if Java is installed.
        """
        try:
            tools.find_executable("java")
        except FileNotFoundError:
            print("Could not find a Java runtime environment on your system.")
            print("Please make sure you installed Java correctly.")

            print("For more information check the LaTeXBuddy manual.")

            raise FileNotFoundError("Unable to find Java runtime environment!")

        try:
            result = tools.find_executable("languagetool")
            executable_source = "native"
        except FileNotFoundError:

            try:
                result = tools.find_executable("languagetool-commandline.jar")
                executable_source = "java"
            except FileNotFoundError:
                print(
                    "Could not find languagetool-commandline.jar in your system's PATH."
                )
                print(
                    "Please make sure you installed languagetool properly and added the"
                )
                print(
                    "directory to your system's PATH variable. Also make sure to make"
                )
                print("the jar-files executable.")

                print("For more information check the LaTeXBuddy manual.")

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

    def check_tex(self, detex_file: Path) -> None:
        """Runs the LanguageTool checks on a file.

        :param detex_file: the detexed file to run checks on
        """

        raw_errors = None

        if self.mode == Mode.LOCAL_SERVER:
            raw_errors = self.lt_post_request(
                detex_file, "http://localhost:" f"{self.local_server.port}" "/v2/check"
            )

        elif self.mode == Mode.REMOTE_SERVER:
            raw_errors = self.lt_post_request(detex_file, self.remote_url)

        elif self.mode == Mode.COMMANDLINE:
            raw_errors = self.execute_commandline_request(detex_file)

        self.format_errors(raw_errors, Path(detex_file))

    def lt_post_request(self, detex_file: Path, server_url: str) -> Optional[Dict]:
        """Send a POST request to the LanguageTool server to check the text.

        :param detex_file: path to the detex'ed file
        :param server_url: URL of the LanguageTool server
        :return: server's response
        """
        if detex_file is None:
            return None

        with open(detex_file) as file:
            text = file.read()

        response = requests.post(
            url=server_url, data={"language": self.language, "text": text}
        )
        return response.json()

    def execute_commandline_request(self, detex_file: Path) -> Optional[Dict]:
        """Execute the LanguageTool command line app to check the text.

        :param detex_file: path to the detex'ed file
        :return: app's response
        """

        if detex_file is None:
            return None

        # cloning list to in order to append the file name
        # w/o changing lt_console_command
        cmd = list(self.lt_console_command)
        cmd.append(str(detex_file))

        output = tools.execute_no_errors(*cmd, encoding="utf_8")

        try:
            json_output = json.loads(output)
        except json.decoder.JSONDecodeError:
            json_output = json.loads("{}")

        return json_output

    def format_errors(self, raw_errors: Dict, detex_file: Path) -> None:
        """Parses LanguageTool errors and converts them to LaTeXBuddy Error objects.

        :param raw_errors: LanguageTool's error output
        :param detex_file: path to the detex'ed file
        """

        if len(raw_errors) == 0:
            return

        tool_name = raw_errors["software"]["name"]

        for match in raw_errors["matches"]:

            context = match["context"]
            context_offset = context["offset"]
            context_end = context["length"] + context_offset
            text = context["text"][context_offset:context_end]
            location = tools.find_char_position(
                self.buddy.file_to_check,
                detex_file,
                self.buddy.charmap,
                match["offset"],
            )

            error_type = "grammar"

            if match["rule"]["category"]["id"] == "TYPOS":
                error_type = "spelling"

            self.errors.append(
                Error(
                    self.buddy,
                    str(self.buddy.file_to_check),
                    tool_name,
                    error_type,
                    match["rule"]["id"],
                    text,
                    location,
                    match["length"],
                    LanguageToolModule.parse_error_replacements(match["replacements"]),
                    False,
                    tool_name + "_" + match["rule"]["id"],
                )
            )

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
            print("Could not find a Java runtime environment on your system.")
            print("Please make sure you installed Java correctly.")

            print("For more information check the LaTeXBuddy manual.")

            raise FileNotFoundError("Unable to find Java runtime environment!")

        try:
            result = tools.find_executable("languagetool-server")
            executable_source = "native"
        except FileNotFoundError:
            try:
                result = tools.find_executable("languagetool-server.jar")
                executable_source = "java"
            except FileNotFoundError:
                print(
                    "Could not find languagetool-commandline.jar in your system's PATH."
                )
                print(
                    "Please make sure you installed languagetool properly and added the"
                )
                print(
                    "directory to your system's PATH variable. Also make sure to make"
                )
                print("the jar-files executable.")

                print("For more information check the LaTeXBuddy manual.")

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

        :param port: port for the server to losten at
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
