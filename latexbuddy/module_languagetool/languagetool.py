import json
import os
import subprocess

import requests

import error_dummy as error
import detex_dummy as detex
import languagetool_local_server as lt_server
from enum import Enum, auto


class Mode(Enum):
    COMMANDLINE = auto()
    LOCAL_SERVER = auto()
    REMOTE_SERVER = auto()


class LanguageToolModule:

    # TODO: implement whitelisting certain rules (exclude multiple whitespaces error by default)
    def __init__(self, mode: Mode = Mode.LOCAL_SERVER, remote_url: str = None, language: str = None):

        self.mode = mode
        self.language = language

        self.local_server = None
        self.remote_url = None
        self.lt_console_command = None

        if self.mode == Mode.LOCAL_SERVER:
            self.local_server = lt_server.LanguageToolLocalServer()
            self.local_server.start_local_server()

        elif self.mode == Mode.REMOTE_SERVER:
            self.remote_url = remote_url  # must include the port and api call (e.g. /v2/check)

        elif self.mode == Mode.COMMANDLINE:
            self.find_languagetool_command()

    def find_languagetool_command(self):
        result = os.popen('which languagetool-commandline.jar').read()

        if not result or "not found" in result:
            print('Could not find languagetool-commandline.jar in your system\'s PATH.')
            print('Please make sure you installed languagetool properly and added the directory to '
                  'your system\'s PATH variable. Also make sure to make the jar-files executable.'
                  'For more information check the LaTeXBuddy manual.')
            raise (Exception('Unable to find languagetool installation!'))

        lt_path = result.splitlines()[0]
        self.lt_console_command = ["java",
                                   "-jar", lt_path,
                                   "--json"]
        if self.language:
            self.lt_console_command.append("-l")
            self.lt_console_command.append(self.language)
        else:
            self.lt_console_command.append("--autoDetect")

    def check_tex(self, file_path: str):

        if self.mode == Mode.LOCAL_SERVER:
            raw_errors = self.send_post_request(file_path, f'http://localhost:{self.local_server.port}/v2/check')

        elif self.mode == Mode.REMOTE_SERVER:
            raw_errors = self.send_post_request(file_path, self.remote_url)

        elif self.mode == Mode.COMMANDLINE:
            raw_errors = self.execute_commandline_request(file_path)

        formatted_errors = LanguageToolModule.format_errors(raw_errors, file_path)
        return formatted_errors

    def send_post_request(self, file_path: str, server_url: str):

        if file_path is None:
            return None

        detex_file = detex.detex(file_path)

        with open(detex_file.name) as file:
            text = file.read()

        response = requests.post(url=server_url, data={"language": "de-DE", "text": text})
        return response.json()

    def execute_commandline_request(self, file_path: str):

        if file_path is None:
            return None

        detex_file = detex.detex(file_path)

        cmd = list(self.lt_console_command)
        cmd.append(detex_file.name)

        # TODO: pipe stderr to /dev/null after finishing tests
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)  # , stderr=subprocess.DEVNULL)
        out, err = process.communicate()
        output = out.decode('ISO8859-1')

        return json.loads(output)

    @staticmethod
    def format_errors(raw_errors, file_path):
        
        errors = []
        tool_name = raw_errors['software']['name']

        for match in raw_errors['matches']:

            offset = match['context']['offset']
            offset_end = offset + match['context']['length']

            error_type = 'grammar'

            if match['rule']['category']['id'] == 'TYPOS':
                error_type = 'spelling'

            errors.append(error.Error(
                file_path,
                tool_name,
                error_type,
                match['rule']['id'],
                match['context']['text'][offset: offset_end],
                match['offset'],
                match['length'],
                LanguageToolModule.parse_error_replacements(match['replacements']),
                False
            ))
            
        return errors

    @staticmethod
    def parse_error_replacements(json_replacements):

        output = []

        for entry in json_replacements:
            output.append(entry['value'])

        return output


if __name__ == "__main__":

    lt_module_local = LanguageToolModule(Mode.LOCAL_SERVER, language='de-DE')
    lt_module_cmd = LanguageToolModule(Mode.COMMANDLINE, language='de-DE')

    es_local = lt_module_local.check_tex("tex_files/05_entwicklungsrichtlinien.tex")
    es_cmd = lt_module_cmd.check_tex("tex_files/05_entwicklungsrichtlinien.tex")

    for i in range(min(len(es_local), len(es_cmd))):
        print(es_local[i])
        print(es_cmd[i])
        print()
