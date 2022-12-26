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

import argparse
import os
from pathlib import Path

import pytest

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.module_loader import ModuleLoader
from tests.pytest_testcases.unit_tests.resources.T1400_dummy_modules.dummy_module_0 import (
    DummyModule0,
)


@pytest.fixture
def script_dir():
    return str(Path(os.path.realpath(__file__)).parents[0])


@pytest.fixture
def config_loader(script_dir):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)

    return ConfigLoader(
        parser.parse_args(
            ["--config", script_dir + "/resources/T1400_config.py"],
        ),
    )


def test_unit_tool_loader(config_loader):
    module_loader = ModuleLoader(
        Path("tests/pytest_testcases/unit_tests/resources/T1400_dummy_modules/"),
    )

    modules = module_loader.load_selected_modules(config_loader)

    assert len(modules) == 1
    assert type(modules[0]) == DummyModule0
