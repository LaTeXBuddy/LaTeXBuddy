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

from latexbuddy.modules.aspell import Aspell
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import (
    ConfigLoader as DriverCL,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_aspell_run_checks(script_dir):
    _ERROR_COUNT = 3  # From aspell commandline output
    document_path = script_dir + "/resources/T1500.txt"
    aspell_instance = Aspell()

    test_file = TexFile(Path(document_path), compile_tex=False)

    output_problems = aspell_instance.run_checks(DriverCL(), test_file)

    assert output_problems[0].text == "speeek"
    assert output_problems[1].text == "tike"
    assert output_problems[2].text == "mesage"
    assert len(output_problems) == _ERROR_COUNT
