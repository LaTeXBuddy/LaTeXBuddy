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

from latexbuddy.modules.own_checkers import EmptySections
from latexbuddy.modules.own_checkers import NativeUseOfRef
from latexbuddy.modules.own_checkers import SiUnitx
from latexbuddy.modules.own_checkers import UnreferencedFigures
from latexbuddy.modules.own_checkers import URLCheck
from latexbuddy.texfile import TexFile
from tests.pytest_testcases.unit_tests.resources.driver_config_loader import (
    ConfigLoader as DriverCL,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


def test_unit_unreferenced_figures_run_checks(script_dir):
    _ERROR_COUNT = 1
    document_path = script_dir + "/resources/T2200.tex"
    checker_instance = UnreferencedFigures()

    test_file = TexFile(Path(document_path), compile_tex=False)

    problems = checker_instance.run_checks(DriverCL(), test_file)

    assert len(problems) == _ERROR_COUNT
    assert str(
        problems[0],
    ) == "Latex info on 17:1: gantt: Figure gantt not referenced.."


def test_unit_si_unit_run_checks(script_dir):
    _ERROR_COUNT = 3
    document_path = script_dir + "/resources/T2200.tex"
    checker_instance = SiUnitx()

    test_file = TexFile(Path(document_path), compile_tex=False)

    output_problems = checker_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == _ERROR_COUNT
    assert (
        str(output_problems[0]) == "Latex info on 4:47: 2021: For number 2021 "
        "\\num from siunitx may be used.."
    )
    assert (
        str(output_problems[1]) == "Latex info on 10:1: 2002: For number 2002 "
        "\\num from siunitx may be used.."
    )


def test_unit_empty_sections_run_checks(script_dir):
    _ERROR_COUNT = 1
    document_path = script_dir + "/resources/T2200.tex"
    checker_instance = EmptySections()

    test_file = TexFile(Path(document_path), compile_tex=False)

    output_problems = checker_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == _ERROR_COUNT
    assert (
        str(output_problems[0]) == "Latex info on None: : Sections may not be "
        "empty.."
    )


def test_unit_url_check_run_checks(script_dir):
    _ERROR_COUNT = 1
    document_path = script_dir + "/resources/T2200.tex"
    checker_instance = URLCheck()

    test_file = TexFile(Path(document_path), compile_tex=False)

    output_problems = checker_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == _ERROR_COUNT
    assert output_problems[0].text == "https://www.tu-braunschweig.de/"


def test_unit_native_use_of_ref_run_checks(script_dir):
    _ERROR_COUNT = 1
    document_path = script_dir + "/resources/T2200.tex"
    checker_instance = NativeUseOfRef()

    test_file = TexFile(Path(document_path), compile_tex=False)

    output_problems = checker_instance.run_checks(DriverCL(), test_file)

    assert len(output_problems) == _ERROR_COUNT
    assert str(output_problems[0]) == \
        R"Latex info on 35:1: " \
        R"\ref{: Instead of \ref{} use a more precise command, " \
        R"for example, \cref{}."
