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
from logging import DEBUG
from pathlib import Path

import pytest

from latexbuddy.buddy import LatexBuddy
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from tests.pytest_testcases.integration_tests.resources.T800_driver_ModuleProvider import DriverModule1
from tests.pytest_testcases.integration_tests.resources.T800_driver_ModuleProvider import DriverModuleProvider


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


@pytest.fixture
def default_config_loader():
    return ConfigLoader()


def test_integration_buddy_module(script_dir, caplog, default_config_loader):
    # initializing logger on DEBUG level
    caplog.set_level(DEBUG)

    LatexBuddy.init(
        default_config_loader,
        DriverModuleProvider(),
        Path(script_dir + "/resources/T800_test_document.tex"),
        [Path(script_dir + "/resources/T800_test_document.tex")],
        compile_tex=False,
    )

    LatexBuddy.run_tools()

    records = "\n".join([record.message for record in caplog.records])

    # asserting that buddy-module communication worked and checks have been started
    assert "Returning scripted module instances." in records
    assert "Using multiprocessing pool with " in records

    # asserting that the correct problem has been returned (unfortunately, due to the
    # checking process being parallelized, the logs during the checks are unavailable)

    problem_list = [
        problem for uid,
        problem in LatexBuddy.instance.errors.items()
    ]
    assert len(problem_list) == 1

    assert problem_list[0] == Problem(
        position=None,
        text="just a general problem",
        checker=DriverModule1,
        file=LatexBuddy.instance.tex_file.plain_file,
        severity=ProblemSeverity.INFO,
    )
