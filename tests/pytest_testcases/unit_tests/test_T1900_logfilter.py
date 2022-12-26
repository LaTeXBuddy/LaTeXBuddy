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
import re
from pathlib import Path
from tempfile import mkstemp

import pytest
from resources.driver_config_loader import ConfigLoader

from latexbuddy.modules.logfilter import LogFilter
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.tools import execute_and_collect


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_logfilter_all_problems_in_texfilt(script_dir):
    # config_path = script_dir + "/resources/T1900_config.py"
    document_path = Path(script_dir + "/resources/T1900.tex")
    texfilt_path = script_dir + "/latexbuddy/modules/texfilt.awk"
    log_filter = LogFilter()
    config_loader = ConfigLoader()
    tex_file = TexFile(document_path)
    descriptor, raw_problems_path = mkstemp(
        prefix="latexbuddy",
        suffix="raw_log_errors",
    )

    problems = log_filter.run_checks(config_loader, tex_file)

    cmd = [
        "awk",
        "-f",
        texfilt_path,
        f"{str(tex_file.log_file)} > {raw_problems_path}",
    ]
    execute_and_collect(*cmd)  # output not used
    raw_problems = Path(raw_problems_path).read_text()

    test = True
    for problem in problems:
        if problem.description is not None:
            test = test and problem.description in raw_problems
    assert test


def test_unit_logfilter_all_texfilt_in_problems(script_dir):
    # config_path = script_dir + "/resources/T1900_config.py"
    document_path = Path(script_dir + "/resources/T1900.tex")
    texfilt_path = script_dir + "/latexbuddy/modules/texfilt.awk"
    log_filter = LogFilter()
    config_loader = ConfigLoader()
    tex_file = TexFile(document_path)
    descriptor, raw_problems_path = mkstemp(
        prefix="latexbuddy",
        suffix="raw_log_errors",
    )

    problems = log_filter.run_checks(config_loader, tex_file)
    problem_line_nos = []
    for problem in problems:
        problem_line_nos.append(problem.position[0])

    cmd = [
        "awk",
        "-f",
        texfilt_path,
        f"{str(tex_file.log_file)} > {raw_problems_path}",
    ]
    execute_and_collect(*cmd)  # output not used
    raw_problems = Path(raw_problems_path).read_text()
    texfilt_problems_split = raw_problems.split(" ")
    problem_re = re.compile(
        r"(?P<line_no>\d+):",
    )

    test = True
    for problem in texfilt_problems_split:
        match = problem_re.match(problem)
        if not match:
            continue
        line_no = match.group("line_no")
        test = test and line_no in problem_line_nos
    assert test
