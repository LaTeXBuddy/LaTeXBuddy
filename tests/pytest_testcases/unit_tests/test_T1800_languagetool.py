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

from latexbuddy.modules.languagetool import LanguageTool
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import (
    ConfigLoader as DriverCL,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_languagetool_run_checks(script_dir):
    _ERROR_COUNT = 16
    document_path = script_dir + "/resources/test_paper.tex"
    languagetool_instance = LanguageTool()

    test_file = TexFile(Path(document_path))

    problems = languagetool_instance.run_checks(DriverCL(), test_file)

    assert len(problems) == _ERROR_COUNT
    assert str(
        problems[0],
    ) == "Grammar error on 15:43:   : Whitespace repetition (bad formatting)."
    assert str(problems[1]) == 'Grammar error on 19:276: ": Smart quotes (“”).'
    assert str(problems[2]) == 'Grammar error on 19:286: ": Smart quotes (“”).'
