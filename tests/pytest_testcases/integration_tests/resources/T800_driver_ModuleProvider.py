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

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.log import Loggable
from latexbuddy.module_loader import ModuleProvider
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.problem import ProblemSeverity
from latexbuddy.texfile import TexFile


class DriverModuleProvider(ModuleProvider, Loggable):
    def load_selected_modules(self, cfg: ConfigLoader) -> list[Module]:
        return self.load_modules()

    def load_modules(self) -> list[Module]:
        self.logger.debug("Returning scripted module instances.")
        return [DriverModule0(), DriverModule1()]


class DriverModule0(Module):
    def __init__(self):
        return

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        self.logger.debug("returning no problems")
        return []


class DriverModule1(Module):
    def __init__(self):
        return

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        return [
            Problem(
                position=None,
                text="just a general problem",
                checker=DriverModule1,
                file=file.plain_file,
                severity=ProblemSeverity.INFO,
            ),
        ]
