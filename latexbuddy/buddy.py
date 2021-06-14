"""This module describes the main LaTeXBuddy instance class."""

import json
import multiprocessing as mp
import os
import time

from pathlib import Path
from typing import AnyStr, List, Optional

import latexbuddy.tools as tools

from latexbuddy import TexFile
from latexbuddy import __logger as root_logger
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.messages import error_occurred_in_module
from latexbuddy.modules import Module
from latexbuddy.preprocessor import Preprocessor
from latexbuddy.problem import Problem, ProblemJSONEncoder


# TODO: make this a singleton class with static methods


class LatexBuddy:
    """The main instance of the applications that controls all the internal tools."""

    __logger = root_logger.getChild("buddy")

    def __init__(self, config_loader: ConfigLoader, file_to_check: Path):
        """Initializes the LaTeXBuddy instance.

        :param config_loader: ConfigLoader object to manage config options
        :param file_to_check: file that will be checked
        """
        self.errors = {}  # all current errors
        self.cfg: ConfigLoader = config_loader  # configuration
        self.file_to_check = file_to_check  # .tex file that is to be error checked
        self.tex_file: TexFile = TexFile(file_to_check)

        # file where the error should be saved
        self.output_dir = Path(
            self.cfg.get_config_option_or_default(
                "buddy", "output", Path("./"), verify_type=AnyStr
            )
        )

        if not self.output_dir.is_dir():
            self.__logger.warning(
                f"'{str(self.output_dir)}' is not a directory. "
                f"Current directory will be used instead."
            )
            self.output_dir = Path.cwd()

        self.output_format = str(
            self.cfg.get_config_option_or_default(
                "buddy",
                "format",
                "HTML",
                verify_type=AnyStr,
                verify_choices=["HTML", "html", "JSON", "json"],
            )
        ).upper()

        # file that represents the whitelist
        self.whitelist_file = Path(
            self.cfg.get_config_option_or_default(
                "buddy", "whitelist", Path("whitelist.json"), verify_type=AnyStr
            )
        )

    def add_error(self, problem: Problem):
        # current language
        self.lang = self.cfg.get_config_option_or_default("buddy", "language", "en")

    def change_file(self, file):
        """Method to change the current file. Used for multi check files included
            in other files

        :param file: the new file to check next
        """
        self.file_to_check = file  # .tex file that is to be error checked
        self.tex_file: TexFile = TexFile(file)

    def add_error(self, error: Problem):
        """Adds the error to the errors dictionary.

        UID is used as key, the error object is used as value.

        :param problem: problem to add to the dictionary
        """

        if self.preprocessor is None or self.preprocessor.matches_preprocessor_filter(
            problem
        ):
            self.errors[problem.uid] = problem

    def check_whitelist(self):
        """Removes errors that are whitelisted."""
        if not (self.whitelist_file.exists() and self.whitelist_file.is_file()):
            return  # if no whitelist yet, don't have to check

        whitelist_entries = self.whitelist_file.read_text().splitlines()

        for uid, problem in self.errors.items():
            if problem.key in whitelist_entries:
                del self.errors[uid]

    def add_to_whitelist(self, uid):
        """Adds the error identified by the given UID to the whitelist

        Afterwards this method deletes all other errors that are the same as the one
        just whitelisted.

        :param uid: the UID of the error to be deleted
        """

        if uid not in self.errors:
            self.__logger.error(
                f"UID not found: {uid}. "
                "Specified problem will not be added to whitelist."
            )
            return

        # write error in whitelist
        with self.whitelist_file.open("a+") as file:
            file.write(self.errors[uid].cid)
            file.write("\n")

        # delete error and save comp_id for further check
        compare_id = self.errors[uid].cid
        del self.errors[uid]

        # check if there are other errors equal to the one just added to the whitelist
        for i_uid, problem in self.errors.items():
            if problem.key == compare_id:
                del self.errors[i_uid]
                break

    # TODO: implement
    # def add_to_whitelist_manually(self):
    #     return

    def mapper(self, module: Module) -> List[Problem]:
        """
        Executes checks for provided module and returns its Problems.
        This method is used to parallelize the module execution.

        :param module: module to execute
        :return: list of resulting problems
        """
        result = []

        def lambda_function() -> None:
            nonlocal result

            start_time = time.perf_counter()
            self.__logger.debug(f"{module.__class__.__name__} started checks")

            result = module.run_checks(self.cfg, self.tex_file)

            self.__logger.debug(
                f"{module.__class__.__name__} finished after "
                f"{round(time.perf_counter() - start_time, 2)} seconds"
            )

        tools.execute_no_exceptions(
            lambda_function,
            error_occurred_in_module(module.__class__.__name__),
            "DEBUG",
        )

        return result

    def run_tools(self):
        """Runs all tools in the LaTeXBuddy toolchain in parallel"""

        # importing this here to avoid circular import error
        from latexbuddy.tool_loader import ToolLoader

        # initialize Preprocessor
        self.preprocessor = Preprocessor()
        self.preprocessor.regex_parse_preprocessor_comments(self.tex_file)

        # initialize ToolLoader
        tool_loader = ToolLoader(Path("latexbuddy/modules/"))
        modules = tool_loader.load_selected_modules(self.cfg)

        self.__logger.debug(
            f"Using multiprocessing pool with {os.cpu_count()} "
            f"threads/processes for checks."
        )

        with mp.Pool(processes=os.cpu_count()) as pool:
            result = pool.map(self.mapper, modules)

        for problems in result:
            for problem in problems:
                self.add_error(problem)

        # FOR TESTING ONLY
        # self.check_whitelist()
        # keys = list(self.errors.keys())
        # for key in keys:
        #     self.add_to_whitelist(key)
        #     return

    def output_json(self):
        """Writes all the current problem objects to the output file."""

        list_of_problems = []

        for problem_uid in self.errors.keys():
            list_of_problems.append(self.errors[problem_uid])

        json_output_path = Path(str(self.output_dir) + "/latexbuddy_output.json")

        with json_output_path.open("w") as file:
            json.dump(list_of_problems, file, indent=4, cls=ProblemJSONEncoder)

        self.__logger.info(f"Output saved to {json_output_path.resolve()}")

    def output_html(self):
        """Renders all current problem objects as HTML and writes the file."""

        # importing this here to avoid circular import error
        from latexbuddy.output import render_html

        html_output_path = Path(str(self.output_dir) + "/latexbuddy_output.html")
        html_output_path.write_text(
            render_html(
                str(self.tex_file.tex_file),
                self.tex_file.tex,
                self.errors,
            )
        )

        self.__logger.info(f"Output saved to {html_output_path.resolve()}")

    def output_file(self):
        """Writes all current problems to the specified output file."""

        if self.output_format == "JSON":
            self.output_json()

        else:  # using HTML as default
            self.output_html()
