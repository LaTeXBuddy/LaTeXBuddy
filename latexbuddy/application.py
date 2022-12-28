#  LaTeXBuddy - a LaTeX checking tool
#  Copyright (c) 2022  LaTeXBuddy
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

import json
import logging
import re
import time
import typing
from pathlib import Path

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.module_loader import ModuleLoader
from latexbuddy.preprocessor import Preprocessor
from latexbuddy.texfile import TexFile

if typing.TYPE_CHECKING:
    from latexbuddy.module_loader import ModuleProvider
    from latexbuddy.problem import Problem

LOG = logging.getLogger(__name__)

# This regex matches the mathematical equations after they've been detex'ed
# away by YaLafi. It replaces evry instance of $...$, $$...$$, etc. with
# a string of three equal uppercase latin letters.
# TODO: put this into the detexer and ignore the problems there
_detexed_equation_re = re.compile(r"^([A-Z])-\1-\1$")


class Application:
    """Abstraction of the LaTeXBuddy application, aka the Runner.

    It collects all data for a single run of the program, which includes
    files, settings, and results.
    """

    def __init__(
        self,
        files: typing.Sequence[Path],
        module_provider: ModuleProvider | None = None,
        config_loader: ConfigLoader | None = None,
        *,
        compile_tex: bool,
    ) -> None:
        """Initializes the application."""

        # start and end time for benchmarking purposes
        self.start_time: float = time.perf_counter()
        self.end_time: float | None = None

        if config_loader is None:
            self.config: ConfigLoader = ConfigLoader()
        else:
            self.config = config_loader

        if module_provider is None:
            self.module_provider = ModuleLoader(
                Path(
                    self.config.get_config_option_or_default(
                        self,
                        "module_dir",
                        "latexbuddy/modules/",
                        verify_type=typing.AnyStr,  # type: ignore
                    ),
                ),
            )
        else:
            self.module_provider = module_provider

        self.modules = module_provider.load_selected_modules(
            self.config,
        )
        self.preprocessor: Preprocessor | None = Preprocessor()
        self.whitelist: Path = Path(
            # FIXME: make config work with the new runner instance
            self.config.get_config_option_or_default(
                self,
                "whitelist",
                "whitelist",
                verify_type=typing.AnyStr,  # type: ignore
            ),
        )

        self.files: typing.Sequence[Path] = files
        self.compile_tex = compile_tex

        self.output_dir = Path(
            # FIXME: make config work with the new runner instance
            self.config.get_config_option_or_default(
                self,
                "output",
                "./latexbuddy_html/",
                verify_type=typing.AnyStr,  # type: ignore
            ),
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_format = str(
            self.config.get_config_option_or_default(
                # FIXME: make config work with the new runner instance
                self,
                "format",
                "HTML",
                verify_type=typing.AnyStr,
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

        # Problems collected during the run
        self.problems: dict[str, Problem] = {}

    def add_problem(
        self,
        problem: Problem,
        preprocessor: Preprocessor | None = None,
    ) -> None:

        if preprocessor is not None:
            if not preprocessor.matches_preprocessor_filter(problem):
                # if preprocessor thinks we should ignore this problem
                return

        if _detexed_equation_re.match(problem.text):
            # if the problem relates to the fact that YaLafi's equation
            # IDs aren't actual words
            return

        self.problems[problem.uid] = problem

    def output_json(self, file: Path) -> None:
        from latexbuddy.problem import ProblemJSONEncoder

        results_file = self.output_dir / f"{file.stem}.result.json"
        with results_file.open("w") as file:
            json.dump(
                self.problems.values(),
                file,
                indent="\t",
                cls=ProblemJSONEncoder,
            )
        LOG.info(
            f"JSON output saved to {results_file.resolve()}",
        )

    def output_html(self, file: Path, tex_file: TexFile) -> None:
        from latexbuddy.output import render_html

        results_file = self.output_dir / f"output_{file.stem}.html"

        if tex_file.pdf_file is None:
            results_file.write_text(
                render_html(
                    file.name,
                    tex_file.tex,
                    self.problems,
                    self.files,
                    str(None),
                ),
            )
        else:
            results_file.write_text(
                render_html(
                    file.name,
                    tex_file.tex,
                    self.problems,
                    self.files,
                    str(tex_file.pdf_file.resolve()),
                ),
            )

    def run_checks(self, file: Path, tex_file: TexFile) -> None:
        preprocessor = Preprocessor()
        preprocessor.regex_parse_preprocessor_comments(
            tex_file,
        )

        # TODO: migrate to multiprocessing later
        for module in self.modules:
            try:
                start_time = time.perf_counter()
                result = module.run_checks(
                    self.config,
                    tex_file,
                )
                LOG.debug(
                    f"{module.display_name} finished after "
                    f"{round(time.perf_counter() - start_time, 3)} seconds",
                )
            except Exception as exc:  # noqa: BLE001
                LOG.error(
                    f"An exception occured while running "
                    f"{module.display_name}",
                )
                LOG.exception(exc)
                continue

            for problem in result:
                self.add_problem(problem)

    def run(self) -> None:
        try:
            for file in self.files:
                tex_file = TexFile(file, compile_tex=self.compile_tex)
                self.run_checks(file, tex_file)
        except KeyboardInterrupt as exc:
            LOG.critical("Caught keyboard interrupt from user")
            LOG.exception(exc)
            raise SystemExit(4) from exc

        self.end_time = time.perf_counter()
        LOG.debug(
            f"Finished after "
            f"{round(self.end_time - self.start_time, 3)} seconds",
        )
