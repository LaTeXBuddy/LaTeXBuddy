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
"""This is an example configuration for LaTeXBuddy and the tools that are
supported out-of-the-box.

You may move this file and specify its path using the --config flag.
"""
from __future__ import annotations

main = {
    "language": "en",
    "language_country": "GB",
    "whitelist": "./tests/pytest_testcases/unit_tests/resources/T1200_whitelist_temp",
    "output": "./latexbuddy_html/",
}

modules = {}
