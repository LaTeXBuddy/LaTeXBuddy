import socket

from contextlib import closing

import requests

import tools


class LanguageToolLocalServer:

    _DEFAULT_PORT = 8081

    def __init__(self):

        self.lt_path = None
        self.lt_server_command = None
        self.server_process = None
        self.port = None

    def __del__(self):

        self.stop_local_server()

    def get_server_port(self):
        return self.port

    def get_server_run_command(self):
        try:
            result = tools.find_executable("languagetool-server.jar")
        except FileNotFoundError:
            print("Could not find languagetool-server.jar in system PATH.")
            print(
                "Please make sure you installed languagetool properly and added the "
                "directory to your system's PATH variable. Also make sure to make "
                "the jar-files executable."
            )
            print("For more information check the LaTeXBuddy manual.")
            raise (Exception("Unable to find languagetool installation!"))

        self.lt_path = result
        self.lt_server_command = [
            "java",
            "-cp",
            self.lt_path,
            "org.languagetool.server.HTTPServer",
            "--port",
            str(self.port),
        ]

    def start_local_server(self, port: int = _DEFAULT_PORT) -> int:

        if self.server_process:
            return -1

        self.port = self.find_free_port(port)

        self.get_server_run_command()

        self.server_process = tools.execute_background_from_list(self.lt_server_command)

        self.wait_till_server_up()

        return self.port

    def wait_till_server_up(self):

        up = False
        while not up:
            try:
                requests.post(f"http://localhost:{self.port}/v2/check")
                up = True

            except requests.RequestException:
                up = False

    def stop_local_server(self):

        if not self.server_process:
            return

        self.server_process.kill()
        self.server_process = None

    @staticmethod
    def find_free_port(port: int = None) -> int:

        if port and not LanguageToolLocalServer.is_port_in_use(port):
            return port

        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("localhost", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    @staticmethod
    def is_port_in_use(port: int) -> bool:

        if not port:
            return True

        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            return s.connect_ex(("localhost", port)) == 0
