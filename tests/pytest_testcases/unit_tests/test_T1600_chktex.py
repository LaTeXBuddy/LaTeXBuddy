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

from latexbuddy.modules.chktex import Chktex
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import (
    ConfigLoader as DriverCL,
)

pytestmark = pytest.mark.skipif(
    shutil.which("chktex") is None,
    reason="ChkTeX not installed",
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_chktex_run_checks(script_dir):
    _ERROR_COUNT = 112
    # added tolerance because of versional differences in ChkTeX
    _ERROR_COUNT_TOLERANCE = 5

    document_path = script_dir + "/resources/T1600.tex"
    chktex_instance = Chktex()

    test_file = TexFile(Path(document_path), compile_tex=False)

    output_problems = chktex_instance.run_checks(DriverCL(), test_file)

    assert _ERROR_COUNT <= len(output_problems)
    assert len(output_problems) <= _ERROR_COUNT + _ERROR_COUNT_TOLERANCE
