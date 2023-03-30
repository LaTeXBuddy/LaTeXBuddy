# LaTeXBuddy - a LaTeX checking tool
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
"""Contains the main LaTeXBuddy instance class."""
from __future__ import annotations

import json
import logging
import multiprocessing as mp
import os
import re
import time
from pathlib import Path
from typing import AnyStr

import latexbuddy.tools
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.messages import error_occurred_in_module
from latexbuddy.module_loader import ModuleProvider
from latexbuddy.modules import MainModule
from latexbuddy.modules import Module
from latexbuddy.preprocessor import Preprocessor
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemJSONEncoder
from latexbuddy.problem import set_language
from latexbuddy.texfile import TexFile
from latexbuddy.tools import classproperty


LOG = logging.getLogger(__name__)

equation_re = re.compile(r"^([A-Z])-\1-\1$")


class LatexBuddy(MainModule):
    """The main instance of the applications that controls all the internal
    tools.

    This is a singleton class with only one instance and exclusively
    static methods.
    """

    __current_instance = None

    def __init__(self) -> None:
        super().__init__()

        self.errors: dict[str, Problem] = {}  # all current errors
        self.cfg: ConfigLoader = ConfigLoader()  # configuration
        # in-file preprocessing
        self.preprocessor: Preprocessor | None = None
        self.module_provider: ModuleProvider | None = None
        # .tex file to be error checked
        self.file_to_check: Path | None = None
        self.tex_file: TexFile | None = None
        self.output_dir: Path | None = None
        self.output_format: str | None = None
        self.whitelist_file: Path | None = None
        # all paths of the files to be used in html
        self.path_list: list[Path] = []
        self.compile_tex: bool

    @classproperty
    def instance(cls) -> LatexBuddy:  # noqa N805
        if cls.__current_instance is None:
            cls.__current_instance = LatexBuddy()
        return cls.__current_instance

    @staticmethod
    def init(
        config_loader: ConfigLoader,
        module_provider: ModuleProvider,
        file_to_check: Path,
        path_list: list[Path],
        *,
        compile_tex: bool,
    ) -> None:
        """Initializes the LaTeXBuddy instance.

        :param config_loader: ConfigLoader object to manage config options
        :param module_provider: ModuleProvider instance as a source of
                                Module instances for running checks on
                                the specified file
        :param file_to_check: file that will be checked
        :param path_list: a list of the paths for the html output
        :param compile_tex: boolean if the tex file should be compiled
        """

        LatexBuddy.instance.errors = {}
        LatexBuddy.instance.cfg = config_loader
        LatexBuddy.instance.preprocessor = None
        LatexBuddy.instance.module_provider = module_provider
        LatexBuddy.instance.file_to_check = file_to_check
        LatexBuddy.instance.tex_file = TexFile(
            file_to_check,
            compile_tex=compile_tex,
        )
        LatexBuddy.instance.path_list = path_list

        # file where the error should be saved
        LatexBuddy.instance.output_dir = Path(
            LatexBuddy.instance.cfg.get_config_option_or_default(
                LatexBuddy,
                "output",
                "./latexbuddy_html/",
                verify_type=AnyStr,  # type: ignore
            ),
        )

        if not LatexBuddy.instance.output_dir.is_dir():
            LOG.warning(
                f"'{str(LatexBuddy.instance.output_dir)}' is not a directory. "
                f"Current directory will be used instead.",
            )
            LatexBuddy.instance.output_dir = Path.cwd()

        LatexBuddy.instance.output_format = str(
            LatexBuddy.instance.cfg.get_config_option_or_default(
                LatexBuddy,
                "format",
                "HTML",
                verify_type=AnyStr,  # type: ignore
                verify_choices=[
                    "HTML",
                    "html",
                    "JSON",
                    "json",
                    "HTML_FLASK",
                    "html_flask",
                ],
            ),
        ).upper()

        # file that represents the whitelist
        LatexBuddy.instance.whitelist_file = Path(
            LatexBuddy.instance.cfg.get_config_option_or_default(
                LatexBuddy,
                "whitelist",
                "whitelist",
                verify_type=AnyStr,  # type: ignore
            ),
        )

    @staticmethod
    def add_error(problem: Problem) -> None:
        """Adds the error to the errors dictionary.

        UID is used as key, the error object is used as value.

        :param problem: problem to add to the dictionary
        """

        pp = LatexBuddy.instance.preprocessor
        if pp is not None and not pp.matches_preprocessor_filter(problem):
            return

        if equation_re.match(problem.text):
            return

        LatexBuddy.instance.errors[problem.uid] = problem

    @staticmethod
    def check_whitelist() -> None:
        """Removes errors that are whitelisted."""

        LOG.debug("Beginning whitelist-check...")
        start_time = time.perf_counter()

        if not (
            LatexBuddy.instance.whitelist_file.exists()
            and LatexBuddy.instance.whitelist_file.is_file()
        ):
            return  # if no whitelist yet, don't have to check

        whitelist_entries = LatexBuddy.instance.whitelist_file\
            .read_text().splitlines()
        # TODO: Ignore emtpy strings in here

        # need to copy here or we get an error deleting
        uids = list(LatexBuddy.instance.errors.keys())
        for uid in uids:
            if LatexBuddy.instance.errors[uid].key in whitelist_entries:
                del LatexBuddy.instance.errors[uid]

        LOG.debug(
            f"Finished whitelist-check in "
            f"{round(time.perf_counter() - start_time, 2)} seconds",
        )

    @staticmethod
    def add_to_whitelist(uid: str) -> None:
        """Adds the error identified by the given UID to the whitelist.

        Afterwards this method deletes all other errors that are
        the same as the one just whitelisted.

        :param uid: the UID of the error to be deleted
        """

        if uid not in LatexBuddy.instance.errors:
            LOG.error(
                f"UID not found: {uid}. "
                "Specified problem will not be added to whitelist.",
            )
            return

        # write error to whitelist
        with LatexBuddy.instance.whitelist_file.open("a+") as file:
            file.write(LatexBuddy.instance.errors[uid].key)
            file.write("\n")

        # save key for further check and remove error
        added_key = LatexBuddy.instance.errors[uid].key
        del LatexBuddy.instance.errors[uid]

        # check if there are other errors equal to the one just added
        # to the whitelist
        uids = list(LatexBuddy.instance.errors.keys())
        for curr_uid in uids:
            if LatexBuddy.instance.errors[curr_uid].key == added_key:
                del LatexBuddy.instance.errors[curr_uid]

    @staticmethod
    def execute_module(module: Module) -> list[Problem]:
        """Executes checks for provided module and returns its Problems. This
        method is used to parallelize the module execution.

        :param module: module to execute
        :return: list of resulting problems
        """
        result = []

        def lambda_function() -> None:
            nonlocal result

            start_time = time.perf_counter()
            LOG.debug(f"{module.display_name} started checks")

            result = module.run_checks(
                LatexBuddy.instance.cfg,
                LatexBuddy.instance.tex_file,
            )

            LOG.debug(
                f"{module.display_name} finished after "
                f"{round(time.perf_counter() - start_time, 2)} seconds",
            )

        latexbuddy.tools.execute_no_exceptions(
            lambda_function,
            error_occurred_in_module(module.display_name),
            "DEBUG",
        )

        return result

    @staticmethod
    def run_tools() -> None:
        """Runs all modules in the LaTeXBuddy toolchain in parallel."""

        language = LatexBuddy.instance.cfg.get_config_option_or_default(
            LatexBuddy,
            "language",
            None,
            verify_type=AnyStr,
        )
        # set global variable in problem.py for key generation
        set_language(language)

        # initialize Preprocessor
        LatexBuddy.instance.preprocessor = Preprocessor()
        LatexBuddy.instance.preprocessor.regex_parse_preprocessor_comments(
            LatexBuddy.instance.tex_file,
        )

        # acquire Module instances
        modules = LatexBuddy.instance.module_provider.load_selected_modules(
            LatexBuddy.instance.cfg,
        )

        LOG.debug(
            f"Using multiprocessing pool with {os.cpu_count()} "
            f"threads/processes for checks.",
        )
        LOG.debug(
            f"Executing the following modules in parallel: "
            f"{[module.display_name for module in modules]}",
        )

        with mp.Pool(processes=os.cpu_count()) as pool:
            result = pool.map(LatexBuddy.instance.execute_module, modules)

        for problems in result:
            for problem in problems:
                LatexBuddy.instance.add_error(problem)

    @staticmethod
    def output_json() -> None:
        """Writes all the current problem objects to the output file."""

        list_of_problems = []

        for problem_uid in LatexBuddy.instance.errors:
            list_of_problems.append(LatexBuddy.instance.errors[problem_uid])

        json_output_path = Path(
            str(LatexBuddy.instance.output_dir) + "/latexbuddy_output.json",
        )

        with json_output_path.open("w") as file:
            json.dump(list_of_problems, file, indent=4, cls=ProblemJSONEncoder)

        LOG.info(
            f"Output saved to {json_output_path.resolve()}",
        )

    @staticmethod
    def output_html() -> None:
        """Renders all current problem objects as HTML and writes the file."""

        # importing this here to avoid circular import error
        from latexbuddy.output import render_html

        html_output_path = Path(
            str(LatexBuddy.instance.output_dir)
            + "/"
            + "output_"
            + str(LatexBuddy.instance.file_to_check.stem)
            + ".html",
        )
        html_output_path.write_text(
            render_html(
                str(LatexBuddy.instance.tex_file.tex_file),
                LatexBuddy.instance.tex_file.tex,
                LatexBuddy.instance.errors,
                LatexBuddy.instance.path_list,
                # TODO: this should be the path (str) where the PDF file
                #  is located
                str(
                    LatexBuddy.instance.tex_file.pdf_file,
                ),
            ),
        )

        LOG.info(
            f"Output saved to {html_output_path.resolve()}",
        )

    @staticmethod
    def output_flask_html() -> None:
        # importing this here to avoid circular import error
        from latexbuddy.output import render_flask_html

        html_output_path = Path(
            str(LatexBuddy.instance.output_dir)
            + "/"
            + "output_"
            + str(LatexBuddy.instance.file_to_check.stem)
            + ".html",
        )
        html_output_path.write_text(
            render_flask_html(
                str(LatexBuddy.instance.tex_file.tex_file),
                LatexBuddy.instance.tex_file.tex,
                LatexBuddy.instance.errors,
                LatexBuddy.instance.path_list,
                # TODO: this should be the path (str) where the PDF file
                #  is located
                str(
                    LatexBuddy.instance.tex_file.pdf_file,
                ),
            ),
        )

        LOG.info(
            f"Output saved to {html_output_path.resolve()}",
        )

    @staticmethod
    def output_file() -> None:
        """Writes all current problems to the specified output file."""

        if LatexBuddy.instance.output_format == "JSON":
            LatexBuddy.output_json()

        elif LatexBuddy.instance.output_format == "HTML_FLASK":
            LatexBuddy.output_flask_html()

        else:  # using HTML as default
            LatexBuddy.output_html()
