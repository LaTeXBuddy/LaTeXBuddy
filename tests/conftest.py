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


@pytest.fixture
def driver_config_loader():
    class ConfigLoader:
        def __init__(self):
            pass

        def get_config_option_or_default(
            self,
            module,
            key: str,
            default_value=None,
            verify_type=None,
            verify_regex=None,
            verify_choices=None,
        ):
            if key == "language":
                return "en"
            if key == "language_country":
                return None
            if key == "mode":
                return "COMMANDLINE"
            if key == "disabled-rules":
                return ""
            if key == "disabled-categories":
                return ""
            if key == "format":
                return "not html"

        def get_config_option(
            self,
            module,
            key: str,
        ):
            if key == "format":
                return "json"

    return ConfigLoader()
