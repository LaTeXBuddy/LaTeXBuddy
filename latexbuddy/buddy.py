"""This module describes the main LaTeXBuddy instance class."""

import json
import multiprocessing as mp
import os
import time

from pathlib import Path
from typing import AnyStr, List, Optional

import latexbuddy.tools as tools

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.messages import error_occurred_in_module
from latexbuddy.modules import MainModule, Module
from latexbuddy.preprocessor import Preprocessor
from latexbuddy.problem import Problem, ProblemJSONEncoder, set_language
from latexbuddy.texfile import TexFile
from latexbuddy.tools import classproperty


class LatexBuddy(MainModule):
    """
    The main instance of the applications that controls all the internal tools.
    This is a singleton class with only one instance and exclusively static methods.
    """

    __current_instance = None

    def __init__(self):
        super().__init__()

        self.errors = {}  # all current errors
        self.cfg: ConfigLoader = ConfigLoader()  # configuration
        self.preprocessor: Optional[Preprocessor] = None  # in-file preprocessing
        self.file_to_check: Optional[Path] = None  # .tex file to be error checked
        self.tex_file: Optional[TexFile] = None
        self.output_dir: Optional[Path] = None
        self.output_format: Optional[str] = None
        self.whitelist_file: Optional[Path] = None
        self.path_list: List[Path] = []  # all paths of the files to be used in html

    @classproperty
    def instance(cls):
        if cls.__current_instance is None:
            cls.__current_instance = LatexBuddy()
        return cls.__current_instance

    @staticmethod
    def init(config_loader: ConfigLoader, file_to_check: Path, path_list: List[Path]):
        """Initializes the LaTeXBuddy instance.

        :param config_loader: ConfigLoader object to manage config options
        :param file_to_check: file that will be checked
        :param path_list: a list of the paths for the html output
        """

        LatexBuddy.instance.errors = {}
        LatexBuddy.instance.cfg = config_loader
        LatexBuddy.instance.preprocessor = None
        LatexBuddy.instance.file_to_check = file_to_check
        LatexBuddy.instance.tex_file = TexFile(file_to_check)
        LatexBuddy.instance.path_list = path_list

        # file where the error should be saved
        LatexBuddy.instance.output_dir = Path(
            LatexBuddy.instance.cfg.get_config_option_or_default(
                LatexBuddy, "output", "./latexbuddy_html/", verify_type=AnyStr
            )
        )

        if not LatexBuddy.instance.output_dir.is_dir():
            LatexBuddy.instance.logger.warning(
                f"'{str(LatexBuddy.instance.output_dir)}' is not a directory. "
                f"Current directory will be used instead."
            )
            LatexBuddy.instance.output_dir = Path.cwd()

        LatexBuddy.instance.output_format = str(
            LatexBuddy.instance.cfg.get_config_option_or_default(
                LatexBuddy,
                "format",
                "HTML",
                verify_type=AnyStr,
                verify_choices=["HTML", "html", "JSON", "json"],
            )
        ).upper()

        # file that represents the whitelist
        LatexBuddy.instance.whitelist_file = Path(
            LatexBuddy.instance.cfg.get_config_option_or_default(
                LatexBuddy, "whitelist", Path("whitelist"), verify_type=AnyStr
            )
        )

    @staticmethod
    def add_error(problem: Problem):
        """Adds the error to the errors dictionary.

        UID is used as key, the error object is used as value.

        :param problem: problem to add to the dictionary
        """

        if (
            LatexBuddy.instance.preprocessor is None
            or LatexBuddy.instance.preprocessor.matches_preprocessor_filter(problem)
        ):
            LatexBuddy.instance.errors[problem.uid] = problem

    @staticmethod
    def check_whitelist():
        """Removes errors that are whitelisted."""
        if not (
            LatexBuddy.instance.whitelist_file.exists()
            and LatexBuddy.instance.whitelist_file.is_file()
        ):
            return  # if no whitelist yet, don't have to check

        whitelist_entries = LatexBuddy.instance.whitelist_file.read_text().splitlines()
        # TODO: Ignore emtpy strings in here

        # need to copy here or we get an error deleting
        uids = list(LatexBuddy.instance.errors.keys())
        for uid in uids:
            if LatexBuddy.instance.errors[uid].key in whitelist_entries:
                del LatexBuddy.instance.errors[uid]

    @staticmethod
    def add_to_whitelist(uid):
        """Adds the error identified by the given UID to the whitelist

        Afterwards this method deletes all other errors that are the same as the one
        just whitelisted.

        :param uid: the UID of the error to be deleted
        """

        if uid not in LatexBuddy.instance.errors:
            LatexBuddy.instance.logger.error(
                f"UID not found: {uid}. "
                "Specified problem will not be added to whitelist."
            )
            return

        # write error to whitelist
        with LatexBuddy.instance.whitelist_file.open("a+") as file:
            file.write(LatexBuddy.instance.errors[uid].key)
            file.write("\n")

        # save key for further check and remove error
        added_key = LatexBuddy.instance.errors[uid].key
        del LatexBuddy.instance.errors[uid]

        # check if there are other errors equal to the one just added to the whitelist
        uids = list(LatexBuddy.instance.errors.keys())
        for curr_uid in uids:
            if LatexBuddy.instance.errors[curr_uid].key == added_key:
                del LatexBuddy.instance.errors[curr_uid]

    @staticmethod
    def mapper(module: Module) -> List[Problem]:
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
            module.logger.debug(f"{module.display_name} started checks")

            result = module.run_checks(
                LatexBuddy.instance.cfg, LatexBuddy.instance.tex_file
            )

            module.logger.debug(
                f"{module.display_name} finished after "
                f"{round(time.perf_counter() - start_time, 2)} seconds"
            )

        tools.execute_no_exceptions(
            lambda_function,
            error_occurred_in_module(module.display_name),
            "DEBUG",
        )

        return result

    @staticmethod
    def run_tools():
        """Runs all tools in the LaTeXBuddy toolchain in parallel"""

        language = LatexBuddy.instance.cfg.get_config_option_or_default(
            LatexBuddy,
            "language",
            None,
            verify_type=AnyStr,
        )
        set_language(language)  # set global variable in problem.py for key generation

        # importing this here to avoid circular import error
        from latexbuddy.tool_loader import ToolLoader

        # initialize Preprocessor
        LatexBuddy.instance.preprocessor = Preprocessor()
        LatexBuddy.instance.preprocessor.regex_parse_preprocessor_comments(
            LatexBuddy.instance.tex_file
        )

        # initialize ToolLoader
        tool_loader = ToolLoader(Path("latexbuddy/modules/"))
        modules = tool_loader.load_selected_modules(LatexBuddy.instance.cfg)

        LatexBuddy.instance.logger.debug(
            f"Using multiprocessing pool with {os.cpu_count()} "
            f"threads/processes for checks."
        )

        with mp.Pool(processes=os.cpu_count()) as pool:
            result = pool.map(LatexBuddy.instance.mapper, modules)

        for problems in result:
            for problem in problems:
                LatexBuddy.instance.add_error(problem)

        # FOR TESTING ONLY
        # LatexBuddy.instance.check_whitelist()
        # keys = list(LatexBuddy.instance.errors.keys())
        # for key in keys:
        #     LatexBuddy.instance.add_to_whitelist(key)
        #     return

    @staticmethod
    def output_json():
        """Writes all the current problem objects to the output file."""

        list_of_problems = []

        for problem_uid in LatexBuddy.instance.errors.keys():
            list_of_problems.append(LatexBuddy.instance.errors[problem_uid])

        json_output_path = Path(
            str(LatexBuddy.instance.output_dir) + "/latexbuddy_output.json"
        )

        with json_output_path.open("w") as file:
            json.dump(list_of_problems, file, indent=4, cls=ProblemJSONEncoder)

        LatexBuddy.instance.logger.info(f"Output saved to {json_output_path.resolve()}")

    @staticmethod
    def output_html():
        """Renders all current problem objects as HTML and writes the file."""

        # importing this here to avoid circular import error
        from latexbuddy.output import render_html

        html_output_path = Path(
            str(LatexBuddy.instance.output_dir)
            + "/"
            + "output_"
            + str(LatexBuddy.instance.file_to_check.stem)
            + ".html"
        )
        html_output_path.write_text(
            render_html(
                str(LatexBuddy.instance.tex_file.tex_file),
                LatexBuddy.instance.tex_file.tex,
                LatexBuddy.instance.errors,
                LatexBuddy.instance.path_list,
                str(
                    LatexBuddy.instance.tex_file.pdf_file
                ),  # TODO: this should be the path (str) where the pdf file is located
            )
        )

        LatexBuddy.instance.logger.info(f"Output saved to {html_output_path.resolve()}")

    @staticmethod
    def output_file():
        """Writes all current problems to the specified output file."""

        if LatexBuddy.instance.output_format == "JSON":
            LatexBuddy.instance.output_json()

        else:  # using HTML as default
            LatexBuddy.instance.output_html()
