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
from pathlib import Path

import pytest

from latexbuddy.modules.proselint_checker import ProseLint
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import (
    ConfigLoader as DriverCL,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_proselint_run_checks(script_dir):
    _ERROR_COUNT = 7
    document_path = script_dir + "/resources/ConfoundedLearning/main.tex"
    proselint_checker_instance = ProseLint()

    test_file = TexFile(Path(document_path), compile_tex=False)

    problems = proselint_checker_instance.run_checks(
        DriverCL(), test_file,
    )

    assert len(problems) == _ERROR_COUNT
    assert str(
        problems[0],
    ) == "Grammar warning on 79:180: o.  : Inconsistent spacing after period (1 vs. 2 spaces).."
    assert str(
        problems[1],
    ) == "Grammar warning on 85:376: s.  : Inconsistent spacing after period (1 vs. 2 spaces).."
    assert str(
        problems[2],
    ) == "Grammar warning on 335:45:  in the long run: 'in the long run' is a cliché.."
