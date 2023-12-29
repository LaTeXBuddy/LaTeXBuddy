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

import logging
import multiprocessing as mp
import os
import re
import time
import traceback
from pathlib import Path
from typing import AnyStr

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.messages import error_occurred_in_module
from latexbuddy.module_loader import ModuleProvider
from latexbuddy.modules import MainModule
from latexbuddy.modules import Module
from latexbuddy.preprocessor import Preprocessor
from latexbuddy.problem import Problem
from latexbuddy.problem import set_language
from latexbuddy.texfile import TexFile

LOG = logging.getLogger(__name__)

equation_re = re.compile(r"^([A-Z])-\1-\1$")

_instance: LatexBuddy | None = None


def get_instance() -> LatexBuddy:
    if _instance is None:
        _msg = "LaTeXBuddy is not initialized"
        raise RuntimeError(_msg)

    return _instance


class LatexBuddy(MainModule):
    """The main instance of the applications that controls all the internal
    tools.

    This is a singleton class with only one instance and exclusively
    static methods.
    """

    def __init__(
        self,
        config_loader: ConfigLoader,
        module_provider: ModuleProvider,
        file_to_check: Path,
        path_list: list[Path],
        *,
        compile_tex: bool,
    ) -> None:
        super().__init__()

        self.errors: dict[str, Problem] = {}
        self.cfg = config_loader
        # in-file preprocessing
        self.preprocessor: Preprocessor | None = None
        self.module_provider = module_provider
        self.file_to_check = file_to_check
        self.path_list = path_list

        # .tex file to be error checked
        self.tex_file = TexFile(
            self.file_to_check,
            compile_tex=compile_tex,
        )

        self.output_dir = Path(
            self.cfg.get_config_option_or_default(
                self.__class__,
                "output",
                "./latexbuddy_html/",
                verify_type=AnyStr,  # type: ignore
            ),
        )
        if not self.output_dir.is_dir():
            LOG.warning(
                "Not a directory: %s\n"
                "Current directory will be used instead.",
                self.output_dir,
            )
            self.output_dir = Path.cwd()

        self.output_format = str(
            self.cfg.get_config_option_or_default(
                self.__class__,
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

        self.whitelist_file = Path(
            self.cfg.get_config_option_or_default(
                self.__class__,
                "whitelist",
                "whitelist",
                verify_type=AnyStr,  # type: ignore
            ),
        )

        global _instance  # noqa: PLW0603
        _instance = self

    def add_problem(self, problem: Problem) -> None:
        """Add problem to the dictionary.

        Problem's UID is used as key, while the problem itself is used
        as value.

        :param problem: problem to add to the dictionary
        """

        if self.preprocessor is not None \
                and not self.preprocessor.matches_preprocessor_filter(problem):
            return

        if equation_re.match(problem.text):
            return

        self.errors[problem.uid] = problem

    def check_whitelist(self) -> None:
        LOG.debug("Beginning whitelist-check...")
        start_time = time.perf_counter()

        if not self.whitelist_file.is_file():
            return

        whitelist_entries = set(self.whitelist_file.read_text().splitlines())

        # TODO: Ignore emtpy strings in here
        for uid, problem in list(self.errors.items()):
            if problem.key in whitelist_entries:
                del self.errors[uid]

        LOG.debug(
            "Finished whitelist-check in %.2f seconds",
            time.perf_counter() - start_time,
        )

    def add_to_whitelist(self, uid: str) -> None:
        """Add an error identified by the given UID to the whitelist.

        Afterwards, this method will delete all other errors that are
        the same as the one just whitelisted.

        :param uid: the UID of the error to be deleted
        """

        if uid not in self.errors:
            LOG.error(
                "UID not found: %s. "
                "Specified problem will not be added to whitelist.",
                uid,
            )
            return

        key = self.errors[uid].key
        with self.whitelist_file.open("a+") as f:
            f.write(key)
            f.write("\n")

        del self.errors[uid]

        for uid, problem in list(self.errors.items()):
            if problem.key == key:
                del self.errors[uid]

    def execute_module(self, module: Module) -> list[Problem]:
        result = []

        start_time = time.perf_counter()
        LOG.debug("%s started checks", module.display_name)

        try:
            result = module.run_checks(
                self.cfg,
                self.tex_file,
            )
        except Exception as e:  # noqa: BLE001
            LOG.error(
                "%s:\n%s: %s",
                error_occurred_in_module(module.display_name),
                e.__class__.__name__,
                getattr(e, "message", e),
            )
            LOG.debug(traceback.format_exc())
        else:
            LOG.debug(
                "%s finished after %.2f seconds",
                module.display_name,
                time.perf_counter() - start_time,
            )

        return result

    def run_tools(self) -> None:
        language = self.cfg.get_config_option_or_default(
            self.__class__,
            "language",
            None,
            verify_type=AnyStr,  # type: ignore
        )
        set_language(language)

        self.preprocessor = Preprocessor()
        self.preprocessor.regex_parse_preprocessor_comments(
            self.tex_file,
        )

        modules = self.module_provider.load_selected_modules(
            self.cfg,
        )

        LOG.debug(
            "Using multiprocessing pool with %d "
            "threads/processes for checks.", os.cpu_count(),
        )
        LOG.debug(
            f"Executing the following modules in parallel: "
            f"{[module.display_name for module in modules]}",
        )

        with mp.Pool(processes=os.cpu_count()) as pool:
            result = pool.map(self.execute_module, modules)

        for problems in result:
            for problem in problems:
                self.add_problem(problem)

    def output_json(self) -> None:
        """Write all problem objects to the output file."""
        import json

        from latexbuddy.problem import ProblemJSONEncoder

        problems = list(self.errors.values())
        output_file = Path(self.output_dir) / "latexbuddy_output.json"

        with output_file.open("w") as fd:
            json.dump(problems, fd, indent=4, cls=ProblemJSONEncoder)

        LOG.info("Output saved to %s", output_file.resolve())

    def output_html(self) -> None:
        """Render problems as HTML and write to file."""
        from latexbuddy.output import render_html

        output_file = self.output_dir / \
            f"output_{self.file_to_check.stem}.html"
        output_file.write_text(
            render_html(
                str(self.tex_file.tex_file),
                self.tex_file.tex,
                self.errors,
                self.path_list,
                str(self.tex_file.pdf_file),
            ),
        )

        LOG.info("Output saved to %s", output_file.resolve())

    def output_flask_html(self) -> None:
        from latexbuddy.output import render_flask_html

        output_file = self.output_dir / \
            f"output_{self.file_to_check.stem}.html"
        output_file.write_text(
            render_flask_html(
                str(self.tex_file.tex_file),
                self.tex_file.tex,
                self.errors,
                self.path_list,
                str(self.tex_file.pdf_file),
            ),
        )

    def output_file(self) -> None:
        """Write all problems to the specified output file."""

        if self.output_format == "JSON":
            self.output_json()
        elif self.output_format == "HTML":
            self.output_html()
        elif self.output_format == "HTML_FLASK":
            self.output_flask_html()
        else:
            _msg = f"Unknown output format: {self.output_format}"
            raise ValueError(_msg)
