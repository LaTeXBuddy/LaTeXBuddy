#  LaTeXBuddy - a LaTeX checking tool
#  Copyright (c) 2023  LaTeXBuddy
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.module_loader import ModuleLoader


@pytest.fixture
def modules_dir(resources_dir: Path) -> Path:
    return resources_dir / "module_loader" / "dummy_modules"


@pytest.fixture
def config_file(resources_dir: Path) -> Path:
    return resources_dir / "module_loader" / "config.py"


def test_load_selected_modules(modules_dir: Path, config_file: Path) -> None:
    module_loader = ModuleLoader(modules_dir)
    config_loader = ConfigLoader(Namespace(config=config_file))

    modules = module_loader.load_selected_modules(config_loader)
    assert len(modules) == 1
    assert modules[0].display_name == "DummyModule0"
