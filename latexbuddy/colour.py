# LaTeXBuddy - a LaTeX checking tool
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
"""This module is a utilitary module that simply defines commonly used colour
codes.

It serves as a lightweight replacement for colours defined in
`colorama`.
"""
from __future__ import annotations

RESET_ALL = "\033[0m"
CYAN = "\033[36m"
BLACK_ON_WHITE = "\033[47;30m"
BLACK_ON_YELLOW = "\033[43;30m"
ON_RED = "\033[41m"
