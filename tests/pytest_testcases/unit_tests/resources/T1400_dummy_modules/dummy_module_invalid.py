from __future__ import annotations

from latexbuddy.config_loader import ConfigLoader
from latexbuddy.modules import Module
from latexbuddy.problem import Problem
from latexbuddy.texfile import TexFile


class DummyModuleInvalid:
    def __init__(self):
        pass

    def run_checks(self, config: ConfigLoader, file: TexFile) -> list[Problem]:
        return []
