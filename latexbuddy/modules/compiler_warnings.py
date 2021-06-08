from typing import List
from pathlib import Path

from latexbuddy.modules import Module
from latexbuddy.config_loader import ConfigLoader
from latexbuddy.problem import Problem, ProblemSeverity
from latexbuddy.texfile import TexFile


class CompilerWarnings(Module):

    def __init__(self):
        self.tool_name = "compiler"

    def run_checks(self, config: ConfigLoader, file: TexFile) -> List[Problem]:
        return []
