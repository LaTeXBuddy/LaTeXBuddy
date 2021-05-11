import json

from enum import Enum, auto

import requests

import latexbuddy.error_class as error
import latexbuddy.languagetool_local_server as lt_server
import latexbuddy.tools as tools


_LANGUAGES = {"de": "de-DE", "en": "en"}


def run(buddy, file):
    # TODO: get settings (mode etc.) from buddy instance (config needed)

    ltm = LanguageToolModule(buddy, language=_LANGUAGES[buddy.get_lang()])
    ltm.check_tex(file)


class Mode(Enum):
    COMMANDLINE = auto()
    LOCAL_SERVER = auto()
    REMOTE_SERVER = auto()


class LanguageToolModule:

    # TODO: implement whitelisting certain rules
    #       (exclude multiple whitespaces error by default)
    def __init__(
        self,
        buddy,
        mode: Mode = Mode.LOCAL_SERVER,
        remote_url: str = None,
        language: str = None,
    ):

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

    def check_tex(self, detex_file: str):

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

    def send_post_request(self, detex_file: str, server_url: str):

        if detex_file is None:
            return None

        with open(detex_file) as file:
            text = file.read()

        response = requests.post(
            url=server_url, data={"language": self.language, "text": text}
        )
        return response.json()

    def execute_commandline_request(self, detex_file: str):

        if detex_file is None:
            return None

        cmd = list(self.lt_console_command)
        cmd.append(detex_file)

        output = tools.execute_no_errors_from_list(cmd, encoding="utf_8")

        return json.loads(output)

    def format_errors(self, raw_errors, detex_file):

        tool_name = raw_errors["software"]["name"]

        for match in raw_errors["matches"]:

            offset = match["context"]["offset"]
            offset_end = offset + match["context"]["length"]

            error_type = "grammar"

            if match["rule"]["category"]["id"] == "TYPOS":
                error_type = "spelling"

            error.Error(
                self.buddy,
                detex_file.removesuffix(".detexed"),
                tool_name,
                error_type,
                match["rule"]["id"],
                match["context"]["text"][offset:offset_end],
                match["offset"],
                match["length"],
                LanguageToolModule.parse_error_replacements(match["replacements"]),
                False,
                # TODO: add compare_id here, see error_class.py
            )

    @staticmethod
    def parse_error_replacements(json_replacements):

        output = []

        for entry in json_replacements:
            output.append(entry["value"])

        return output
