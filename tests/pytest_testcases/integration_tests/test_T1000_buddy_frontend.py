# LaTeXBuddy tests
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
from __future__ import annotations

import os
import tempfile
from argparse import Namespace
from pathlib import Path
from typing import AnyStr

import pytest

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules.aspell import Aspell
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from tests.pytest_testcases.integration_tests.resources.T800_driver_ModuleProvider import (
    DriverModuleProvider,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


@pytest.fixture
def temp_dir():
    return tempfile.mkdtemp()


@pytest.fixture
def config_loader(script_dir, temp_dir):
    return ConfigLoader(
        Namespace(
            config=Path(script_dir) / "resources/T1000_config.py",
            output=temp_dir,
            format="HTML",
        ),
    )


@pytest.fixture
def problem_list(script_dir):
    return (
        [
            Problem(
                (4, 7),
                "document",
                Aspell,
                Path(script_dir + "/resources/T1000_test_document.tex"),
                ProblemSeverity.ERROR,
                description="Hi, I am a problem...",
                suggestions=["ldkjfnglsdbliv"],
            ),
            Problem(
                (5, 21),
                "packages",
                Aspell,
                Path(script_dir + "/resources/T1000_test_document.tex"),
                ProblemSeverity.WARNING,
                description="Hi, I am a problem too...",
                suggestions=["goijsfzchbsrlt"],
            ),
        ],
        ["ldkjfnglsdbliv", "goijsfzchbsrlt"],
    )


def test_integration_buddy_frontend(script_dir, problem_list, config_loader):
    buddy = LatexBuddy(
        config_loader,
        DriverModuleProvider(),
        Path(script_dir + "/resources/T1000_test_document.tex"),
        [Path(script_dir + "/resources/T1000_test_document.tex")],
        compile_tex=False,
    )

    for problem in problem_list[0]:
        buddy.add_problem(problem)

    buddy.output_file()

    temp_dir = config_loader.get_config_option(
        LatexBuddy, "output", verify_type=AnyStr,
    )

    with open(temp_dir + "/output_T1000_test_document.html") as file:
        contents = file.read()

        for suggestion_code in problem_list[1]:
            assert suggestion_code in contents
