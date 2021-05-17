"""This module defines the connection between LaTeXBuddy and LanguageTool."""

import json

from enum import Enum, auto
from pathlib import PurePath, Path
from typing import Dict, List, Optional

import requests

import latexbuddy.error_class as error
import latexbuddy.languagetool_local_server as lt_server
import latexbuddy.tools as tools

# TODO: define for all languages or let users choose it
_LANGUAGES = {"de": "de-DE", "en": "en-GB"}


def run(buddy, file: str):
    """Runs the LanguageTool checks on a file and saves the results in a LaTeXBuddy
    instance.

    Requires LanguageTool server to be set up. Local or global servers can be used.

    :param buddy: the LaTeXBuddy instance
    :param file: the file to run checks on
    """
    # TODO: get settings (mode etc.) from buddy instance (config needed)

    ltm = LanguageToolModule(buddy, language=_LANGUAGES[buddy.lang])
    ltm.check_tex(file)


class Mode(Enum):
    """Describes the LanguageTool mode.

    LanguageTool can be run as a command line program, a local server, or a remote
    server.
    """

    COMMANDLINE = auto()
    LOCAL_SERVER = auto()
    REMOTE_SERVER = auto()


# TODO: rewrite this using the Abstract Module API
class LanguageToolModule:
    """Wraps the LanguageTool API calls to check files."""

    # TODO: implement whitelisting certain rules
    #       (exclude multiple whitespaces error by default)
    def __init__(
        self,
        buddy,
        mode: Mode = Mode.COMMANDLINE,
        remote_url: str = None,
        language: str = None,
    ):
        """Creates a LanguageTool checking module.

        :param buddy: the LaTeXBuddy instance
        :param mode: LT mode
        :param remote_url: URL of the LT server
        :param language: language to run checks with
        """
        self.buddy = buddy
        self.mode = mode
        self.language = language

        self.local_server = None
        self.remote_url = None
        self.lt_console_command = None

        if self.mode == Mode.LOCAL_SERVER:
            self.local_server = lt_server.LanguageToolLocalServer()
            self.local_server.start_local_server()

        elif self.mode == Mode.REMOTE_SERVER:
            # must include the port and api call (e.g. /v2/check)
            self.remote_url = remote_url

        elif self.mode == Mode.COMMANDLINE:
            self.find_languagetool_command()

    def find_languagetool_command(self):
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
            result = tools.find_executable("languagetool-commandline.jar")
        except FileNotFoundError:
            print("Could not find languagetool-commandline.jar in your system's PATH.")
            print("Please make sure you installed languagetool properly and added the ")
            print("directory to your system's PATH variable. Also make sure to make ")
            print("the jar-files executable.")

            print("For more information check the LaTeXBuddy manual.")

            raise FileNotFoundError("Unable to find languagetool installation!")

        lt_path = result
        self.lt_console_command = ["java", "-jar", lt_path, "--json"]
        if self.language:
            self.lt_console_command.append("-l")
            self.lt_console_command.append(self.language)
        else:
            self.lt_console_command.append("--autoDetect")

    # TODO: use pathlib.Path
    def check_tex(self, detex_file: Path):
        """Runs the LanguageTool checks on a file.

        :param detex_file: the detexed file to run checks on
        """

        raw_errors = None

        if self.mode == Mode.LOCAL_SERVER:
            raw_errors = self.send_post_request(
                detex_file, "http://localhost:" f"{self.local_server.port}" "/v2/check"
            )

        elif self.mode == Mode.REMOTE_SERVER:
            raw_errors = self.send_post_request(detex_file, self.remote_url)

        elif self.mode == Mode.COMMANDLINE:
            raw_errors = self.execute_commandline_request(detex_file)

        self.format_errors(raw_errors, detex_file)

    # TODO: rename method; current name unclear
    # TODO: use pathlib.Path
    def send_post_request(self, detex_file: str, server_url: str) -> Optional[Dict]:
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

    # TODO: use pathlib.Path
    def execute_commandline_request(self, detex_file: Path) -> Optional[Dict]:
        """Execute the LanguageTool command line app to check the text.

        :param detex_file: path to the detex'ed file
        :return: app's response
        """

        if detex_file is None:
            return None

        # TODO: is that needed here? lt_console_command is already a list
        cmd = list(self.lt_console_command)
        cmd.append(str(detex_file))

        output = tools.execute_no_errors(*cmd, encoding="utf_8")

        return json.loads(output)

    def format_errors(self, raw_errors: Dict, detex_file: Path):
        """Parses LanguageTool errors and converts them to LaTeXBuddy Error objects.

        :param raw_errors: LanguageTool's error output
        :param detex_file: path to the detex'ed file
        """

        tool_name = raw_errors["software"]["name"]

        for match in raw_errors["matches"]:

            context = match["context"]
            context_offset = context["offset"]
            context_end = context["length"] + context_offset
            text = context["text"][context_offset:context_end]
            location = tools.find_char_position(self.buddy.file_to_check,
                                                detex_file,
                                                self.buddy.charmap, match["offset"])

            error_type = "grammar"

            if match["rule"]["category"]["id"] == "TYPOS":
                error_type = "spelling"

            error.Error(
                self.buddy,
                PurePath(detex_file).stem,
                tool_name,
                error_type,
                match["rule"]["id"],
                match["context"]["text"][offset:offset_end],
                match["offset"],
                match["length"],
                LanguageToolModule.parse_error_replacements(match["replacements"]),
                False,
                tool_name + "_" + match["rule"]["id"],
            )

    @staticmethod
    def parse_error_replacements(json_replacements: List[Dict]) -> List[str]:
        """Converts LanguageTool's replacements to LaTeXBuddy suggestions list.

        :param json_replacements: list of LT's replacements for a particular word
        :return: list of string values of said replacements
        """
        output = []

        for entry in json_replacements:
            output.append(entry["value"])

        return output
