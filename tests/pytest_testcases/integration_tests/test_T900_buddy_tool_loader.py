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
from latexbuddy.module_loader import ModuleLoader


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


@pytest.fixture
def default_config_loader():
    return ConfigLoader()


def test_integration_buddy_tool_loader(script_dir, caplog, default_config_loader):
    # initializing logger on DEBUG level
    caplog.set_level(DEBUG)

    LatexBuddy.init(
        default_config_loader,
        ModuleLoader(Path("latexbuddy/modules/")),
        Path(script_dir + "/resources/T900_test_document.tex"),
        [Path(script_dir + "/resources/T900_test_document.tex")],
        compile_tex=False,
    )

    LatexBuddy.run_tools()

    records = "\n".join([record.message for record in caplog.records])

    # asserting that all available modules are being executed (since there is no
    # config file that disables any modules)

    assert (
        "Executing the following modules in parallel: ['Aspell', "
        "'BibtexDuplicates', 'NewerPublications', 'Chktex', 'Diction', "
        "'LanguageTool', 'LogFilter', 'CheckFigureResolution', 'EmptySections',"
        " 'NativeUseOfRef', 'SiUnitx', 'URLCheck', 'UnreferencedFigures',"
        " 'ProseLint', 'YaLafi']" in records
    )
