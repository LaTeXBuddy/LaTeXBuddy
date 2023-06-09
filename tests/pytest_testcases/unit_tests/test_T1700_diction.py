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
import shutil
from pathlib import Path

import pytest

from latexbuddy.modules.diction import Diction
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import (
    ConfigLoader as DriverCL,
)


pytestmark = pytest.mark.skipif(
    shutil.which("diction") is None,
    reason="Diction not installed",
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


@pytest.mark.xfail()
def test_unit_diction_run_checks(script_dir):
    _ERROR_COUNT = 3
    document_path = script_dir + "/resources/T1700.txt"
    diction_instance = Diction()

    test_file = TexFile(Path(document_path), compile_tex=False)

    output_problems = diction_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == _ERROR_COUNT
    assert output_problems[0].text == "This Sentence cause a double double Word Error."
    assert (
        output_problems[1].text == "This Sentence causes a Error, thats why its "
        "important."
    )
