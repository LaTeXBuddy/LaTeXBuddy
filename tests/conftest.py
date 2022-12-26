# LaTeXBuddy tests
# Copyright (C) 2022  LaTeXBuddy
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
"""Test configuration for pytest."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)
    return output_dir


@pytest.fixture
def empty_whitelist_file(tmp_path: Path) -> Path:
    whitelist_file = tmp_path / "whitelist"
    whitelist_file.touch()
    return whitelist_file
